from typing import Dict, Any
from models.result import DecisionResult, DecisionStatus


class ResponseBuilder:
    """
    Formats DecisionResult into 1 single clean Embed presentation without clutter.
    Enforces Strict Rule: Links are ONLY included when the source is an official Discord message.
    No links for DB/Handbook documents.
    """

    @staticmethod
    def build_embed_dict(result: DecisionResult) -> Dict[str, Any]:
        if result.status == DecisionStatus.VERIFIED:
            msg = result.selected_source

            is_live_discord = msg.id.startswith("discord_") if msg else False
            source_label = f"#{msg.channel_name}" if (msg and is_live_discord) else (msg.channel_name if msg else "Thông báo")

            if is_live_discord and msg.message_url and msg.message_url.startswith("http"):
                url_markdown = f"\n\n🔗 **[Link tin nhắn thông báo gốc]({msg.message_url})**"
            else:
                url_markdown = ""

            return {
                "title": "✅ Thông tin đã xác minh",
                "color": 0x2ECC71,  # Green
                "description": f"{result.answer}{url_markdown}",
                "fields": [
                    {"name": "Đối tượng", "value": msg.cohort if msg else "ALL", "inline": True},
                    {"name": "Trạng thái", "value": "Đang có hiệu lực", "inline": True},
                    {"name": "Nguồn", "value": source_label, "inline": True},
                    {"name": "Thời điểm", "value": msg.posted_at[:16].replace("T", " ") if msg else "N/A", "inline": False}
                ],
                "footer": f"ID Truy Vấn: {result.verification_details.get('query_params', {}).get('request_id', 'N/A')}"
            }

        elif result.status == DecisionStatus.VERIFIED_WITH_CONFLICT_RESOLVED:
            msg = result.selected_source
            is_live_discord = msg.id.startswith("discord_") if msg else False
            source_label = f"#{msg.channel_name}" if (msg and is_live_discord) else (msg.channel_name if msg else "Thông báo")

            if is_live_discord and msg.message_url and msg.message_url.startswith("http"):
                url_markdown = f"\n\n🔗 **[Link tin nhắn thông báo gốc]({msg.message_url})**"
            else:
                url_markdown = ""

            rejected_text_list = []
            for rej in result.rejected_sources:
                rej_msg = rej.source
                rej_date = rej_msg.posted_at[:10]
                rej_label = f" (#{rej_msg.channel_name})" if rej_msg.id.startswith("discord_") else f" ({rej_msg.channel_name})"
                rejected_text_list.append(f"• **{rej_date}**{rej_label}: {rej.reason}")

            rejected_str = "\n".join(rejected_text_list) if rejected_text_list else "Không có"

            return {
                "title": "🔎 Đã xử lý thông tin mâu thuẫn",
                "color": 0x3498DB,  # Blue
                "description": f"{result.answer}{url_markdown}",
                "fields": [
                    {
                        "name": "Nguồn chọn",
                        "value": f"{source_label} (Cập nhật: {msg.posted_at[:16].replace('T', ' ') if msg else 'N/A'})",
                        "inline": False
                    },
                    {
                        "name": "Các nguồn bị loại & Lý do",
                        "value": rejected_str,
                        "inline": False
                    }
                ],
                "footer": f"Độ tin cậy: {int(result.confidence * 100)}%"
            }

        else:  # INSUFFICIENT_EVIDENCE
            return {
                "title": "⚠️ Chưa đủ bằng chứng",
                "color": 0xE74C3C,  # Red
                "description": result.answer or "Hiện chưa tìm thấy thông báo hoặc tài liệu chính thức đủ tin cậy để trả lời câu hỏi này.",
                "fields": [
                    {
                        "name": "Khuyến nghị",
                        "value": "Vui lòng bấm nút **Chuyển Mod** bên dưới để gửi ticket tới kênh `#mod-support` xác minh.",
                        "inline": False
                    }
                ],
                "footer": "Trạng thái: Cần xác minh thủ công"
            }
