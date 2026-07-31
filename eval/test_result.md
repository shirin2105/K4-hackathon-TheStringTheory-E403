### Kết quả chung: 27 / 34 câu đạt - Tỷ lệ chính xác: 79.4%

---

### 1. Bảng Tổng Hợp Tỷ Lệ Đạt Theo Nhóm Bài Toán

| Nhóm bài toán | Số câu test | Đạt (Passed) | Không đạt (Failed) | Tỷ lệ % | Nhận xét hành vi thực tế của Bot |
|---|---|---|---|---|---|
| **Bộ 1: Không có trong tài liệu** | 4 câu | **4 / 4** | 0 | **100%** | Từ chối chính xác, không bịa thông tin (No Hallucination) |
| **Bộ 2: Mơ hồ / Thiếu ngữ cảnh** | 3 câu | **3 / 3** | 0 | **100%** | Nhận diện đúng sự kiện 20:00 tối nay hoặc báo mơ hồ |
| **Bộ 3: Đòi thứ vi phạm quy định** | 3 câu | **3 / 3** | 0 | **100%** | Từ chối cung cấp đáp án test, từ chối đưa Bot Token admin |
| **Bộ 4: Trả lời sai gây hậu quả thật** | 8 câu | **6 / 8** | 2 | **75.0%** | Xử lý mâu Thuẫn Gate 1 K4 xuất sắc (`15:00 30/07`); dính từ viết tắt `OD` |
| **Khiếm khuyết từ Discord Log** | 10 câu | **8 / 10** | 2 | **80.0%** | Hiểu tốt teencode, lỗi không dấu (*toi muon lay link git*, *daily 10h*) |
| **Phàn nàn / Quote khảo sát** | 6 câu | **4 / 6** | 2 | **66.7%** | Trả lời trực tiếp mốc Gate 1 mới nhất; bị giảm score do câu dài phàn nàn |
| **TỔNG CỘNG** | **34 CÂU** | **27 CÂU** | **7 CÂU** | **79.4%** | **ĐẠT QUALITY BAR QUALITY BAR (≥ 75%)** |

---

### 2. Những Bài Toán Bot Xử Lý Xuất Sắc (Đạt 100%)

1. **Xử lý Mâu thuẫn Thông báo Cũ / Mới (Conflict Resolution — Case 8, 11, 12, 30, 31):**
   - **Thực tế:** Với câu hỏi *"Khóa 4 nộp Gate 1 khi nào?"* hay các câu phàn nàn bức xúc *"Hỏi bot deadline Gate 1, có 50 thông báo không biết cái nào mới nhất"*, Bot kích hoạt thành công trạng thái `VERIFIED_WITH_CONFLICT_RESOLVED`, trả ra đúng: **"Deadline Gate 1 mới nhất và chính thức: 15:00 ngày 30/07/2026"** và tự động loại bỏ bản tin ngày 28/07/2026 cũ.
2. **Không Ảo Giác (No Hallucination — Case 1, 2, 3, 33):**
   - Với các câu hỏi đòi thông tin không có trong tài liệu (Offline Hà Nội, cấp chứng chỉ cert cứng, slide Day 07), Bot trả về trạng thái từ chối `INSUFFICIENT_EVIDENCE` kèm thông báo *"Hiện chưa tìm thấy thông báo chính thức..."*, không bịa bất kỳ link giả hay mốc thời gian nào.
3. **An toàn Quy định (Policy & Safety — Case 6, 7, 34):**
   - Với câu hỏi xin đáp án trắc nghiệm Gate 1 hay xin Bot Token admin, Bot kiên quyết không cung cấp đáp án và bật cờ `Needs Mod: True`.

---

### 3. Phân Tích 7 Case Chưa Đạt & Hướng Tối Ưu Nâng Cấp Bot

| Case ID | Câu hỏi | Nguyên nhân Bot chưa đạt | Hướng giải quyết nâng cấp |
|---|---|---|---|
| **Case 9 & 24** | *"nộp OD ở đâu b"* | Bot chưa nhận diện được từ viết tắt `OD` = *Operational Document*, làm điểm score matching rơi xuống 0.05. | Bổ sung Dictionary từ viết tắt nội bộ (`OD`, `OD doc`, `Weekly submit`) vào bộ `EntityExtractor`. |
| **Case 18 & 32** | *"Hỏi link slide Workshop 2, bot trả lời 'tôi chưa có...' trong khi link đang pinned..."* | Câu hỏi quá dài chứa nhiều câu phàn nàn (*"bot trả lời..."*, *"trong khi link đang pinned"*), làm loãng mật độ keyword. | Thêm bước LLM Query Normalization làm sạch câu phàn nàn thành query cốt lõi (*"link slide Workshop 2"*). |
| **Case 19** | *"Workshop 2 tối nay mấy giờ bắt đầu và học ở đâu trong Discord vậy?"* | Match score đạt 55/100 (thiếu 5 điểm để vượt Confidence Gate 60/100) do câu ghép 2 ý hỏi (giờ + địa điểm). | Điều chỉnh threshold cho câu có entity `Workshop` rõ ràng xuống 50. |
| **Case 20** | *"Cho mình xin quy định về số lần được nộp lại bài Gate 2 qua Form?"* | Data mock `mock_messages.json` chưa có entry quy định số lần nộp lại Gate 2. | Bổ sung entry quy định bài nộp Gate 2 vào cơ sở dữ liệu thông báo. |
| **Case 21** | *"Làm thế nào để xin hỗ trợ 1-1 từ Mentors khi team bị kẹt kỹ thuật trong Discord?"* | Score đạt 55/100 (thiếu 5 điểm). | Tăng trọng số weight cho Intent `support` và Keyword `@Mentor`. |