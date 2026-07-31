import os
import discord
from models.result import DecisionResult, DecisionStatus


class VerifiedResultView(discord.ui.View):
    """
    Buttons view for CASE VERIFIED.
    """
    def __init__(self, result: DecisionResult):
        super().__init__(timeout=300)
        self.result = result

        if (
            result.should_show_source_link
            and result.selected_source
            and result.selected_source.message_url
            and result.selected_source.message_url.startswith(("http://", "https://"))
        ):
            self.add_item(discord.ui.Button(
                label="Mở nguồn",
                url=result.selected_source.message_url,
                style=discord.ButtonStyle.link
            ))

    @discord.ui.button(label="Xem cách xác minh", style=discord.ButtonStyle.secondary, custom_id="btn_verify_details")
    async def view_verification_details(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg = self.result.selected_source
        details_text = (
            "📌 **Tiêu chí xác minh thông tin:**\n"
            f"• **Cohort:** {msg.cohort} (Được cộng điểm phù hợp cohort)\n"
            f"• **Nguồn phát hành:** {msg.author_name} ({msg.author_role.upper()})\n"
            f"• **Thời điểm đăng:** {msg.posted_at[:16].replace('T', ' ')}\n"
            f"• **Trạng thái:** {msg.status.upper()} (Không bị đánh dấu expired/superseded)\n"
            f"• **Điểm đánh giá tổng:** {self.result.verification_details.get('total_score', 0):.1f}/100"
        )
        await interaction.response.send_message(details_text, ephemeral=True)


class ConflictResultView(discord.ui.View):
    """
    Buttons view for CASE CONFLICT RESOLVED.
    """
    def __init__(self, result: DecisionResult):
        super().__init__(timeout=300)
        self.result = result

        if (
            result.should_show_source_link
            and result.selected_source
            and result.selected_source.message_url
            and result.selected_source.message_url.startswith(("http://", "https://"))
        ):
            self.add_item(discord.ui.Button(
                label="Mở nguồn chính",
                url=result.selected_source.message_url,
                style=discord.ButtonStyle.link
            ))

    @discord.ui.button(label="Xem các nguồn đã loại", style=discord.ButtonStyle.secondary, custom_id="btn_rejected_sources")
    async def view_rejected_sources(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.result.rejected_sources:
            await interaction.response.send_message("Không có nguồn nào bị loại.", ephemeral=True)
            return

        lines = ["🔎 **Danh sách các nguồn mâu thuẫn bị loại:**"]
        for idx, rej in enumerate(self.result.rejected_sources[:5], 1):
            src = rej.source
            ch_name = f"#{src.channel_name}" if src.id.startswith("discord_") else src.channel_name
            lines.append(
                f"{idx}. **[{src.id}]** ({src.posted_at[:10]} - {ch_name})\n"
                f"   • Nội dung: \"{src.content[:60]}...\"\n"
                f"   • **Lý do loại:** {rej.reason}"
            )

        output_text = "\n\n".join(lines)
        if len(output_text) > 1900:
            output_text = output_text[:1900] + "\n...(Đã cắt gọn để vừa giới hạn Discord)"

        await interaction.response.send_message(output_text, ephemeral=True)


class InsufficientResultView(discord.ui.View):
    """
    Buttons view for CASE INSUFFICIENT EVIDENCE.
    Forwards tickets directly to MOD_CHANNEL_ID!
    """
    def __init__(self, result: DecisionResult):
        super().__init__(timeout=300)
        self.result = result

    @discord.ui.button(label="Chuyển Mod", style=discord.ButtonStyle.danger, custom_id="btn_forward_mod")
    async def forward_to_mod(self, interaction: discord.Interaction, button: discord.ui.Button):
        req_id = self.result.verification_details.get('query_params', {}).get('request_id', 'REQ-MOD')
        q_text = self.result.verification_details.get('query_params', {}).get('question', 'N/A')

        mod_channel_id = os.getenv("MOD_CHANNEL_ID", "").strip()
        ticket_posted = False

        if mod_channel_id:
            try:
                mod_channel = interaction.client.get_channel(int(mod_channel_id))
                if mod_channel:
                    mod_embed = discord.Embed(
                        title="🚨 YÊU CẦU HỖ TRỢ XÁC MINH (TICKET CẦN MOD)",
                        description=f"**Mã Yêu Cầu:** `{req_id}`\n**Người hỏi:** {interaction.user.mention}\n**Kênh gửi:** {interaction.channel.mention}",
                        color=0xE74C3C
                    )
                    mod_embed.add_field(name="Câu hỏi chưa có bằng chứng", value=f"\"{q_text}\"", inline=False)
                    mod_embed.set_footer(text="Vui lòng đăng thông báo chính thức hoặc phản hồi học viên.")
                    await mod_channel.send(embed=mod_embed)
                    ticket_posted = True
            except Exception as e:
                print(f"[Mod Channel Error]: {e}")

        button.disabled = True
        button.label = "Đã chuyển Mod"
        await interaction.response.edit_message(view=self)

        mod_confirm_text = (
            "✅ **Yêu cầu đã được gửi đến Đội ngũ Mod!**\n"
            f"• **Mã Ticket:** `{req_id}`\n"
        )
        if ticket_posted:
            mod_confirm_text += "• **Kênh tiếp nhận:** Thông báo đã được tạo trực tiếp trong kênh Mod Support.\n"
        else:
            mod_confirm_text += "• **Trạng thái:** Đã ghi nhận hệ thống cần Mod xác minh.\n"

        mod_confirm_text += "Đội ngũ Mod sẽ rà soát và phản hồi sớm nhất."
        await interaction.followup.send(mod_confirm_text, ephemeral=True)

    @discord.ui.button(label="Xem nguồn đã tìm thấy", style=discord.ButtonStyle.secondary, custom_id="btn_candidates")
    async def view_candidates(self, interaction: discord.Interaction, button: discord.ui.Button):
        candidates = self.result.candidate_sources
        if not candidates:
            await interaction.response.send_message("Không tìm thấy thông báo liên quan trong cơ sở dữ liệu.", ephemeral=True)
            return

        lines = ["📋 **Các nguồn liên quan tìm thấy (chưa đủ độ tin cậy):**"]
        for idx, src in enumerate(candidates[:5], 1):
            ch_name = f"#{src.channel_name}" if src.id.startswith("discord_") else src.channel_name
            lines.append(f"{idx}. **[{src.id}]** ({ch_name}): \"{src.content[:80]}\" (Cohort: {src.cohort})")

        output_text = "\n".join(lines)
        if len(output_text) > 1900:
            output_text = output_text[:1900] + "\n...(Đã cắt gọn để vừa giới hạn Discord)"

        await interaction.response.send_message(output_text, ephemeral=True)
