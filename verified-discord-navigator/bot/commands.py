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
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="sources", description="Xem toàn bộ nguồn và điểm số đánh giá liên quan.")
    @app_commands.describe(question="Nội dung câu hỏi để rà soát nguồn")
    async def sources_command(self, interaction: discord.Interaction, question: str):
        if not interaction.response.is_done():
            try:
                await interaction.response.defer(ephemeral=True)
            except Exception:
                pass

        all_messages = await self.get_all_sources()
        result = self.engine.process_query(question=question, messages=all_messages)
        if not result.candidate_sources:
            await interaction.followup.send("Không tìm thấy nguồn nào liên quan.", ephemeral=True)
            return

        lines = [f"📊 **Báo cáo nguồn cho:** *\"{question}\"*"]
        lines.append(f"• Intent: `{result.verification_details.get('query_params', {}).get('intent')}`")
        lines.append(f"• Cohort: `{result.verification_details.get('query_params', {}).get('cohort')}`")
        lines.append(f"• Trạng thái xử lý: `{result.status.value}`\n")

        lines.append("**Danh sách nguồn candidate:**")
        for idx, src in enumerate(result.candidate_sources, 1):
            src_label = f"#{src.channel_name}" if not src.id.startswith("doc_") else src.channel_name
            url_str = f" - [Link]({src.message_url})" if src.message_url else ""
            lines.append(
                f"{idx}. **[{src.id}]** {src_label} (Cohort: {src.cohort}, Status: {src.status}){url_str}\n"
                f"   \"{src.content}\""
            )

        await interaction.followup.send("\n".join(lines), ephemeral=True)

    @app_commands.command(name="demo", description="Chạy thử 3 case demo bắt buộc của hackathon.")
    @app_commands.describe(case="Chọn case demo")
    async def demo_command(
        self,
        interaction: discord.Interaction,
        case: Literal["verified", "conflict", "insufficient"]
    ):
        if not interaction.response.is_done():
            try:
                await interaction.response.defer()
            except Exception:
                pass

        demo_questions = {
            "verified": "Workshop tối nay lúc mấy giờ?",
            "conflict": "Khóa 4 nộp Gate 1 khi nào?",
            "insufficient": "Tuần sau có workshop đặc biệt không?"
        }

        question = demo_questions[case]
        all_messages = await self.get_all_sources()
        result = self.engine.process_query(question=question, messages=all_messages)
        embed = create_result_embed(result)

        if result.status == DecisionStatus.VERIFIED:
            view = VerifiedResultView(result)
        elif result.status == DecisionStatus.VERIFIED_WITH_CONFLICT_RESOLVED:
            view = ConflictResultView(result)
        else:
            view = InsufficientResultView(result)

        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="health", description="Kiểm tra trạng thái hoạt động của bot.")
    async def health_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Bot đang hoạt động bình thường (Verified Discord Navigator CP2).")
