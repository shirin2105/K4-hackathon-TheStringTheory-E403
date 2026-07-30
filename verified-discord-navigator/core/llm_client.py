import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


class DeepSeekClient:
    """
    DeepSeek LLM Integration Client using standard library HTTP.
    Uses model: deepseek-chat (DeepSeek V3 Flash/Chat).
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
            "max_tokens": 512
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(DEEPSEEK_API_URL, data=data_bytes, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
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

    def synthesize_answer(self, question: str, source_content: str, cohort: str) -> str:
        """
        Synthesizes a clear, ultra-specific answer directly from verified source message.
        """
        system_prompt = (
            "Bạn là trợ lý xác minh thông tin Discord khóa học. "
            "Hãy đưa ra CÂU TRẢ LỜI CỤ THỂ, TRỰC TIẾP và RÕ RÀNG cho câu hỏi dựa vào thông báo nguồn được cung cấp. "
            "Đưa thẳng kết quả (ví dụ ngày giờ/deadline/link) lên dòng đầu tiên. "
            "Ngắn gọn dưới 40 từ, chính xác 100% theo nguồn, tuyệt đối không suy đoán."
        )

        user_prompt = f"Câu hỏi: {question}\nNguồn chính thức ({cohort}): {source_content}"
        ans = self._call_api(system_prompt, user_prompt, json_mode=False)
        return ans.strip() if ans else source_content
