import os
import asyncio
import logging
import discord
from discord import app_commands
from discord.ext import commands
from typing import Literal

from core.decision_engine import DecisionEngine
from bot.embeds import create_result_embed
from bot.views import VerifiedResultView, ConflictResultView, InsufficientResultView
from models.result import DecisionStatus

logger = logging.getLogger("NavigatorCommands")


class NavigatorCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, engine: DecisionEngine):
        self.bot = bot
        self.engine = engine

    async def get_all_sources(self):
        """
        Retrieves live messages from official announcement channel 1532306560871567390
        combined with course documents database.
        """
        ann_channel_id = os.getenv("ANNOUNCEMENT_CHANNEL_ID", "1532306560871567390").strip()
        live_messages = []
        if ann_channel_id:
            live_messages = await self.engine.retriever.fetch_live_messages_async(self.bot, ann_channel_id)

        db_messages = self.engine.retriever.load_all_messages()
        return live_messages + db_messages

    @app_commands.command(name="ask", description="Hỏi bot để tìm thông tin, deadline, workshop đã được xác minh.")
    @app_commands.describe(question="Nội dung câu hỏi của bạn")
    async def ask_command(self, interaction: discord.Interaction, question: str):
        if not interaction.response.is_done():
            try:
                await interaction.response.defer()
            except Exception:
                logger.exception("Failed to defer slash-command response")

        try:
            all_messages = await self.get_all_sources()
            result = await asyncio.to_thread(
                self.engine.process_query,
                question=question,
                user_id=str(interaction.user.id),
                channel_id=str(interaction.channel_id),
                messages=all_messages,
            )

            embed = create_result_embed(result)
            if result.status == DecisionStatus.VERIFIED:
                view = VerifiedResultView(result)
            elif result.status == DecisionStatus.VERIFIED_WITH_CONFLICT_RESOLVED:
                view = ConflictResultView(result)
            else:
                view = InsufficientResultView(result)

            await interaction.followup.send(embed=embed, view=view)
        except Exception as err:
            logger.exception("Error handling slash command: %s", err)
            try:
                await interaction.followup.send(
                    "⚠️ Có lỗi xảy ra trong quá trình xử lý câu hỏi. Vui lòng thử lại sau ít phút.",
                    ephemeral=True,
                )
            except Exception:
                logger.exception("Failed to send slash-command error response")

    @app_commands.command(name="status", description="Xem trạng thái hệ thống xác minh và độ tin cậy.")
    async def status_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛡️ Trạng Thái Hệ Thống Verified Discord Navigator",
            color=0x10b981
        )
        embed.add_field(name="Động cơ Scoring", value="8-Factor DecisionEngine", inline=True)
        embed.add_field(name="Ngưỡng Tin Cậy (Gate)", value="≥ 60.0 Score", inline=True)
        embed.add_field(name="Mẫu Giám Sát", value="Top 5 Candidates", inline=True)
        embed.add_field(name="Kênh Thông Báo Live", value="<#1532306560871567390>", inline=False)
        embed.set_footer(text="Verified Discord Navigator • AI20K Build Phase")

        await interaction.response.send_message(embed=embed, ephemeral=True)
