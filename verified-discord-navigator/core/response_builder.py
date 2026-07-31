from typing import Dict, Any
from models.result import DecisionResult, DecisionStatus


class ResponseBuilder:
    """
    Formats DecisionResult into 1 single clean Embed presentation without clutter.
    Enforces Strict User Rule: When a verified answer is found, do NOT show 'Nguồn chọn',
    'Các nguồn bị loại & Lý do', or unnecessary links. Keep response clean and direct.
    """

    @staticmethod
    def build_embed_dict(result: DecisionResult) -> Dict[str, Any]:
        if result.status in [DecisionStatus.VERIFIED, DecisionStatus.VERIFIED_WITH_CONFLICT_RESOLVED]:
            return {
                "title": "✅ Thông tin đã xác minh",
                "color": 0x2ECC71,  # Green
                "description": f"{result.answer}",
                "fields": [],
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
