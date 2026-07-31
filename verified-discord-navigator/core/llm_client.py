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
    Enforces Strict User Rules:
    1. Scope: Only answer course-related questions / tasks. Refuse non-course queries.
    2. Format: Correct & Complete, Ultra-concise, Direct, No filler or greetings.
    3. Links: No document links unless official Discord message.
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
            "- intent: 'deadline' | 'schedule' | 'workshop' | 'document' | 'submission' | 'regulation' | 'out_of_scope' | 'unknown'\n"
            "- cohort: 'K2' | 'K3' | 'K4' | 'ALL' | 'UNKNOWN'\n"
            "- topic: string ngắn gọn (vd 'Gate 1', 'Workshop', 'CP2') hoặc null\n"
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
        Synthesizes answer adhering strictly to the 3 User Rules:
        Rule 1: Only answer course-related questions. Politely refuse non-course questions.
        Rule 2: Correct, complete, concise, easy to understand. No filler, greetings, or extra words.
        Rule 3: No fake or document links.
        """
        if current_time_str is None:
            current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        system_prompt = (
            "Bạn là Trợ lý AI Phản hồi Khóa học AI20K Build Phase.\n"
            f"Thời điểm hiện tại của hệ thống: {current_time_str}.\n\n"
            "TUÂN THỦ BẮT BUỘC 3 QUY TẮC PHẢN HỒI:\n\n"
            "QUY TẮC 1 - CHỈ TRẢ LỜI CÂU HỎI VỀ KHÓA HỌC:\n"
            "Nếu câu hỏi KHÔNG LIÊN QUAN đến khóa học hay việc cần làm của khóa học (ví dụ: thời tiết, tán gẫu, tin tức ngoài, giải toán...), "
            "bạn PHẢI TỪ CHỐI ngắn gọn đúng câu sau: 'Xin lỗi, tôi là Trợ lý Khóa học và chỉ hỗ trợ giải đáp các thắc mắc, lịch trình, bài tập và quy định liên quan đến khóa học.'\n\n"
            "QUY TẮC 2 - ĐÚNG VÀ ĐỦ, NGẮN GỌN DỄ HIỂU:\n"
            "Trả lời ĐÚNG VÀ ĐỦ, KHÔNG THỪA KHÔNG THIẾU. Đưa thẳng kết quả/danh sách công việc/deadline lên dòng đầu tiên. "
            "Không thêm lời chào hỏi rườm rà (ví dụ 'Chào bạn', 'Dưới đây là...'), không giải thích dông dài hay dùng lời hoa mỹ thừa thải.\n\n"
            "QUY TẮC 3 - KHÔNG TỰ TẠO LINK GIẢ:\n"
            "Chỉ trích dẫn thông tin văn bản. Không tự tạo thêm link tài liệu nếu trong nguồn không có sẵn."
        )

        user_prompt = f"Thời điểm hiện tại: {current_time_str}\nCâu hỏi: {question}\nCohort: {cohort}\n\nTOP NGUỒN TRÍCH XUẤT:\n{source_content}"
        ans = self._call_api(system_prompt, user_prompt, json_mode=False)
        return ans.strip() if ans else source_content
