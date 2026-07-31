from typing import Dict, Any
from models.result import DecisionResult, DecisionStatus


class ResponseBuilder:
    """
    Formats DecisionResult into 1 single clean Embed presentation without clutter.
    Enforces Strict User Rule: When a verified answer is found, do NOT show 'Nguồn chọn',
    'Các nguồn bị loại & Lý do', or unnecessary links. Keep response clean and direct.
    """

    MAX_DESCRIPTION_LENGTH = 4096

    @staticmethod
    def _source_link(result: DecisionResult) -> str:
        source = result.selected_source
        if not result.should_show_source_link or not source or not source.message_url.startswith(("https://", "http://")):
            return ""
        return f"\n\n[🔗 Xem thông báo gốc]({source.message_url})"

    @staticmethod
    def _bounded_description(answer: str) -> str:
        if len(answer) <= ResponseBuilder.MAX_DESCRIPTION_LENGTH:
            return answer
        return answer[:ResponseBuilder.MAX_DESCRIPTION_LENGTH - 1].rstrip() + "…"

    @staticmethod
    def build_embed_dict(result: DecisionResult) -> Dict[str, Any]:
        if result.status in [DecisionStatus.VERIFIED, DecisionStatus.VERIFIED_WITH_CONFLICT_RESOLVED]:
            source_link = ResponseBuilder._source_link(result)
            answer_limit = ResponseBuilder.MAX_DESCRIPTION_LENGTH - len(source_link)
            answer = result.answer
            if len(answer) > answer_limit:
                answer = answer[:answer_limit - 1].rstrip() + "…"
            return {
                "title": "✅ Thông tin đã xác minh",
                "color": 0x2ECC71,  # Green
                "description": answer + source_link,
                "fields": [],
                "footer": f"Độ tin cậy: {int(result.confidence * 100)}%"
            }

        else:  # INSUFFICIENT_EVIDENCE
            return {
                "title": "⚠️ Chưa đủ bằng chứng",
                "color": 0xE74C3C,  # Red
                "description": ResponseBuilder._bounded_description(
                    result.answer or "Hiện chưa tìm thấy thông báo hoặc tài liệu chính thức đủ tin cậy để trả lời câu hỏi này."
                ),
                "fields": [
                    {
                        "name": "Khuyến nghị",
                        "value": "Vui lòng bấm nút **Chuyển Mod** bên dưới để gửi ticket tới kênh `#mod-support` xác minh.",
                        "inline": False
                    }
                ],
                "footer": "Trạng thái: Cần xác minh thủ công"
            }
