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
    Strategy: Strict No-Filler, Strict Scope & Time Comparison Guardrail.
    - Answers ONLY what is explicitly asked.
    - Compares posted_at date against current_time to avoid mistaking yesterday's 'tối nay' for today!
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
            "max_tokens": 1000
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(DEEPSEEK_API_URL, data=data_bytes, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[DeepSeek API Error]: {e}")
            return ""

    def analyze_query(self, question: str) -> Dict[str, Any]:
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
        Synthesizes answer following strict No-Filler, No-Unasked-Info, and Time Comparison Guardrails.
        """
        if current_time_str is None:
            current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        system_prompt = (
            "Bạn là Trợ lý AI Phản hồi Khóa học AI20K Build Phase.\n"
            f"Thời điểm hiện tại của hệ thống: {current_time_str}.\n\n"
            "QUY TẮC NGHÊM NGẶT (TUYỆT ĐỐI TUÂN THỦ):\n"
            "1. SO SÁNH THỜI GIAN ĐĂNG VÀ THỜI GIAN HIỆN TẠI (TIME COMPARISON GUARDRAIL):\n"
            "   - BẮT BUỘC so sánh ngày đăng bài (`Thời điểm đăng`) của thông báo với Ngày hiện tại (`Thời điểm hiện tại`).\n"
            "   - Nếu một thông báo ghi 'tối nay', 'hôm nay' ĐƯỢC ĐĂNG VÀO NGÀY HÔM QUA (ví dụ đăng ngày 30/07/2026 nhưng ngày hiện tại là 31/07/2026): Bạn BẮT BUỘC phải trích dẫn thời gian trong thông báo kèm ngày đăng rõ ràng. Ví dụ: 'Theo thông báo mới nhất từ BTC (đăng ngày 30/07/2026), workshop diễn ra lúc 20:00 (cho tối 30/07). Hiện chưa có thông báo mới cho hôm nay (31/07/2026).'\n"
            "   - TUYỆT ĐỐI KHÔNG khẳng định thông báo ngày hôm qua là của 'tối nay' (ngày hiện tại) mà phải nêu rõ ngày đăng bài.\n"
            "2. ĐÚNG VÀ ĐỦ - KHÔNG THỪA THÔNG TIN KHÔNG ĐƯỢC HỎI:\n"
            "   - Chỉ trả lời chính xác điều được hỏi trong câu hỏi. TUYỆT ĐỐI KHÔNG tự động chèn thêm các hướng dẫn quy trình phụ (như quy trình fork repo, hướng dẫn nộp lab chung...) nếu người dùng KHÔNG hỏi.\n"
            "   - Với câu hỏi về lịch trình ('hôm nay làm gì', 'workshop tối nay'): CHỈ liệt kê các sự kiện thuộc HÔM NAY. KHÔNG tự bịa hoặc lấy thông báo cũ làm thông báo mới.\n"
            "3. RETRIEVE FIRST - GIẢI ĐÁP KHÁI NIỆM KHÓA HỌC:\n"
            "   - Trả lời thẳng vào định nghĩa và công dụng khái niệm (XP, Rank, Gate...).\n"
            "4. TỪ CHỐI CÂU HỎI NGOÀI KHÓA HỌC:\n"
            "   - Từ chối ngắn gọn đúng câu nếu ngoài phạm vi khóa học.\n"
            "5. KHÔNG CHÈN LINK GIẢ HOẶC LINK KHÔNG ĐƯỢC YÊU CẦU."
        )

        user_prompt = f"Thời điểm hiện tại: {current_time_str}\nCâu hỏi: {question}\nCohort: {cohort}\n\nTOP NGUỒN TRÍCH XUẤT:\n{source_content}"
        ans = self._call_api(system_prompt, user_prompt, json_mode=False)
        return ans.strip() if ans else source_content
