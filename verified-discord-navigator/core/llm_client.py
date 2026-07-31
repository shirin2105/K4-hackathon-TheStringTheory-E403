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
    Strategy: RETRIEVE FIRST, DECIDE SECOND.
    - If retrieved course knowledge base or announcements contain relevant information (XP, Codelabs, Gate, Bài lab, Rank...): Answer directly & concisely.
    - Only if retrieved sources contain NO relevant info AND query is completely unrelated to course: Politely refuse.
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
        Synthesizes answer following the 'Retrieve First, Decide Second' principle.
        """
        if current_time_str is None:
            current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        system_prompt = (
            "Bạn là Trợ lý AI Phản hồi Khóa học AI20K Build Phase.\n"
            f"Thời điểm hiện tại của hệ thống: {current_time_str}.\n\n"
            "QUY TẮC XỬ LÝ (RETRIEVE FIRST, DECIDE SECOND):\n"
            "1. Đọc kỹ TOP NGUỒN TRÍCH XUẤT được cung cấp bên dưới (gồm Thông báo live và Cơ sở Tri thức khóa học chứa thông tin về XP, Codelabs, Gate, Bài lab, Rank, Ticket...).\n"
            "2. NẾU TRONG NGUỒN CÓ THÔNG TIN GIẢI ĐÁP (kể cả định nghĩa/công dụng của XP, EXP, Rank, Quy trình làm bài lab...):\n"
            "   -> Trả lời ĐÚNG VÀ ĐỦ, NGẮN GỌN DỄ HIỂU. Đưa thẳng định nghĩa, công dụng hoặc danh sách công việc lên đầu. Không chào hỏi hay giải thích rườm rà.\n"
            "3. CHỈ NẾU TRONG NGUỒN KHÔNG CÓ THÔNG TIN VÀ CÂU HỎI HOÀN TOÀN KHÔNG LIÊN QUAN ĐẾN KHÓA HỌC (thời tiết, tán gẫu, bóng đá, toán học ngoài...):\n"
            "   -> Từ chối ngắn gọn đúng câu: 'Xin lỗi, tôi là Trợ lý Khóa học và chỉ hỗ trợ giải đáp các thắc mắc, lịch trình, bài tập và quy định liên quan đến khóa học.'\n"
            "4. KHÔNG DẪN LINK KHÔNG PHẢI LINK THÔNG BÁO DISCORD GỐC. Không tự bịa ra thông tin ngoài các nguồn được cung cấp."
        )

        user_prompt = f"Thời điểm hiện tại: {current_time_str}\nCâu hỏi: {question}\nCohort: {cohort}\n\nTOP NGUỒN TRÍCH XUẤT:\n{source_content}"
        ans = self._call_api(system_prompt, user_prompt, json_mode=False)
        return ans.strip() if ans else source_content
