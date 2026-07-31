import os
import discord
from discord import app_commands
from discord.ext import commands
from typing import Literal

from core.decision_engine import DecisionEngine
from bot.embeds import create_result_embed
from bot.views import VerifiedResultView, ConflictResultView, InsufficientResultView
from models.result import DecisionStatus


class NavigatorCommands(commands.Cog):
    def __init__(self, bot: commands.Bot, engine: DecisionEngine):
        self.bot = bot
        self.engine = engine

    async def get_all_sources(self):
        """
        Retrieves live messages from official announcement channel 1527920171963125953
        combined with course documents database.
        """
        ann_channel_id = os.getenv("ANNOUNCEMENT_CHANNEL_ID", "1527920171963125953").strip()
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
                pass

        all_messages = await self.get_all_sources()

        result = self.engine.process_query(
            question=question,
            user_id=str(interaction.user.id),
            channel_id=str(interaction.channel_id),
            messages=all_messages
        )

        embed = create_result_embed(result)

        if result.status == DecisionStatus.VERIFIED:
            view = VerifiedResultView(result)
        elif result.status == DecisionStatus.VERIFIED_WITH_CONFLICT_RESOLVED:
            view = ConflictResultView(result)
        else:
            view = InsufficientResultView(result)

        # Send EXACTLY 1 single clean response message
        try:
            await interaction.followup.send(embed=embed, view=view)
        except Exception:
            try:
                await interaction.channel.send(embed=embed, view=view)
            except Exception:
                pass

    @app_commands.command(name="status", description="Xem trạng thái hệ thống xác minh và độ tin cậy.")
    async def status_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛡️ Trạng Thái Hệ Thống Verified Discord Navigator",
            color=0x10b981
        )
        embed.add_field(name="Động cơ Scoring", value="8-Factor DecisionEngine", inline=True)
        embed.add_field(name="Ngưỡng Tin Cậy (Gate)", value="≥ 60.0 Score", inline=True)
        embed.add_field(name="Mẫu Giám Sát", value="Top 5 Candidates", inline=True)
        embed.add_field(name="Kênh Thông Báo Live", value="<#1527920171963125953>", inline=False)
        embed.set_footer(text="Verified Discord Navigator • AI20K Build Phase")

        await interaction.response.send_message(embed=embed, ephemeral=True)
