import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from datetime import datetime

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


class DeepSeekClient:
    """
    DeepSeek LLM Integration Client using standard library HTTP.
    Uses model: deepseek-chat (DeepSeek V3 Flash/Chat).
    Strategy: Strict No-Filler & Strict Scope.
    - Answers ONLY what is explicitly asked.
    - Never appends unasked handbook tutorials, guidelines, or extra tips.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            self.api_key = "sk-eaca2234980f48b09ebbf5121c6c0b82"

    def _call_api(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload: Dict[str, Any] = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(DEEPSEEK_API_URL, data=data_bytes, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[DeepSeek API Error]: {e}")
            return ""

    def analyze_query(self, question: str) -> Dict[str, Any]:
        """
        Uses DeepSeek Chat to extract intent, cohort, topic, date_reference, resource_type in JSON.
        """
        system_prompt = (
            "Bạn là AI phân tích truy vấn cho hệ thống Discord khoá học. "
            "Hãy phân tích câu hỏi và trả về duy nhất 1 JSON object có các trường:\n"
            "- intent: 'deadline' | 'schedule' | 'workshop' | 'document' | 'submission' | 'regulation' | 'unknown'\n"
            "- cohort: 'K2' | 'K3' | 'K4' | 'ALL' | 'UNKNOWN'\n"
            "- topic: string ngắn gọn (vd 'Gate 1', 'XP', 'CP2') hoặc null\n"
            "- date_reference: string (vd 'tối nay', 'tuần sau') hoặc null\n"
            "- resource_type: string (vd 'slide', 'link', 'repo') hoặc null\n\n"
            "Chỉ trả về JSON thuần, không thêm markdown hay giải thích."
        )

        resp_text = self._call_api(system_prompt, f"Câu hỏi: \"{question}\"", json_mode=True)
        if not resp_text:
            return {}

        try:
            return json.loads(resp_text)
        except Exception:
            return {}

    def synthesize_answer(self, question: str, source_content: str, cohort: str, current_time_str: Optional[str] = None) -> str:
        """
        Synthesizes answer following strict No-Filler, No-Unasked-Info principles.
        """
        if current_time_str is None:
            current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        system_prompt = (
            "Bạn là Trợ lý AI Phản hồi Khóa học AI20K Build Phase.\n"
            f"Thời điểm hiện tại của hệ thống: {current_time_str}.\n\n"
            "QUY TẮC NGHÊM NGẶT (TUYỆT ĐỐI TUÂN THỦ):\n"
            "1. ĐÚNG VÀ ĐỦ - KHÔNG THỪA THÔNG TIN KHÔNG ĐƯỢC HỎI:\n"
            "   - Chỉ trả lời chính xác điều được hỏi trong câu hỏi. TUYỆT ĐỐI KHÔNG tự động chèn thêm các hướng dẫn quy trình phụ (như quy trình fork repo, hướng dẫn nộp lab chung...) nếu người dùng KHÔNG hỏi.\n"
            "   - Với các câu hỏi về lịch trình/công việc ('hôm nay làm gì', 'hôm nay phải làm gì', 'lịch hôm nay'): CHỈ liệt kê đúng các sự kiện/deadline/workshop có mốc thời gian là HÔM NAY. KHÔNG liệt kê hướng dẫn quy trình chung.\n"
            "2. RETRIEVE FIRST - GIẢI ĐÁP KHÁI NIỆM KHÓA HỌC:\n"
            "   - Nếu câu hỏi hỏi về khái niệm/quy định trong khóa học (XP, EXP, Rank, Gate, Ticket, Codelabs...): Trả lời đi thẳng vào định nghĩa và công dụng, không chào hỏi dông dài.\n"
            "3. TỪ CHỐI CÂU HỎI NGOÀI KHÓA HỌC:\n"
            "   - Nếu câu hỏi không có trong nguồn và hoàn toàn không liên quan khóa học (thời tiết, tán gẫu...), từ chối ngắn gọn đúng câu: 'Xin lỗi, tôi là Trợ lý Khóa học và chỉ hỗ trợ giải đáp các thắc mắc, lịch trình, bài tập và quy định liên quan đến khóa học.'\n"
            "4. KHÔNG CHÈN LINK GIẢ HOẶC LINK KHÔNG ĐƯỢC YÊU CẦU."
        )

        user_prompt = f"Thời điểm hiện tại: {current_time_str}\nCâu hỏi: {question}\nCohort: {cohort}\n\nTOP NGUỒN TRÍCH XUẤT:\n{source_content}"
        ans = self._call_api(system_prompt, user_prompt, json_mode=False)
        return ans.strip() if ans else source_content
