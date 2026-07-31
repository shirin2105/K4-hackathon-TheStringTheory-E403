# AI SPEC — Verified Discord Navigator · Nhóm The String Theory · Hướng B
Hướng: [ ] A — VLearn  [x] B — Trợ lý Học viên  [ ] C — Làn mở
Loại: [x] Tối ưu tính năng có sẵn  [ ] Tính năng mới

## §1. User & Job
- Job executor + workflow: Học viên K3 & K4 đang học khoá VLearn trên Discord. Workflow: Gặp câu hỏi logistics (deadline, link, lịch) → gõ vào Discord hỏi bot → đọc câu trả lời → thực hiện.
- Core JTBD: Nhận được câu trả lời **đúng, cụ thể, có căn cứ nguồn chính thức** cho câu hỏi logistics ngay trong Discord — không phải tự đi tìm trong đống thông báo.
- Problem statement: Bot Discord hiện tại **không thể trả lời trực tiếp** thông tin từ kênh thông báo chính thức. Khi học viên hỏi deadline hoặc link, bot chỉ tag tên kênh (`#thong-bao`) rồi bảo người dùng tự vào đọc. Kết quả: học viên phải scroll qua 40–50 tin nhắn, gặp nhiều thông báo cùng topic nhưng khác ngày, không biết cái nào mới nhất — rủi ro đọc sai thông báo đã bị thay thế, dẫn đến nộp bài sai deadline.
- Evidence (chuẩn B — mining data Discord):
  - Số liệu mining: Qua đọc chatlog Discord khoá, phát hiện bot trả về redirect link (tag kênh + bảo tự đọc) thay vì câu trả lời cụ thể trong phần lớn câu hỏi logistics. Học viên mất trung bình 2–5 phút tự tìm thông tin sau khi nhận redirect, so với kỳ vọng ≤10 giây nếu bot trả lời thẳng.
  - ≥5 quote/ví dụ nguyên văn + nguồn:
    1. "Hỏi bot deadline Gate 1, nó bảo vào #thong-bao xem — tôi vào thì có 50 thông báo, không biết cái nào mới nhất" (kênh #hoi-dap)
    2. "Bot tag #venture-arena xong nói tự đọc đi, nhưng trong đó có 3 thông báo Gate 1 khác nhau, tôi không biết cái nào đúng" (kênh #hoi-dap)
    3. "Hỏi link slide Workshop 2, bot trả lời 'tôi chưa có thông tin cụ thể, bạn kiểm tra kênh thông báo' — trong khi link slide đang pinned ngay trong #thong-bao" (kênh #general)
    4. "Bot không trả lời được deadline, cứ redirect tôi đi chỗ khác, cuối cùng tôi phải hỏi TA" (kênh #hoi-dap)
    5. "Câu trả lời của bot là một link, không phải một câu trả lời — tôi vẫn phải tự đọc hết trang đó" (kênh #cohort-4)

## §2. Impact & quyết định chọn
- Bảng impact ≥3 ứng viên:
  | Ứng viên | Bao nhiêu người | Tần suất | Mỗi lần tốn gì | Khả thi |
  |---|---|---|---|---|
  | 1. Bot tổng hợp & trả lời thẳng từ kênh thông báo chính thức | ~10.000 học viên K3 & K4 | 5–10 lần/ngày/người | 2–5 phút tự tìm + rủi ro đọc thông báo sai | Cao |
  | 2. Bot phát hiện mâu thuẫn giữa các thông báo cùng topic | ~10.000 học viên K3 & K4 | Khi có thông báo cập nhật | Đọc nhầm thông báo cũ, sai deadline | Cao |
  | 3. Bot tự động reply bằng cách copy nguyên thông báo | ~10.000 học viên K3 & K4 | 5–10 lần/ngày/người | Phản hồi dài, không chọn lọc, trả cả thông báo cũ | Thấp (chưa có xử lý mâu thuẫn) |
- Ứng viên ĐÃ LOẠI + vì sao:
  - (3) Copy nguyên thông báo: Không phân biệt thông báo mới/cũ, không tổng hợp nội dung liên quan — học viên vẫn phải tự đọc toàn bộ thông báo dài.
- Ứng viên CHỌN + vì sao:
  - (1) + (2) kết hợp: Truy xuất đúng thông báo liên quan → chấm điểm độ ưu tiên (authority, cohort, freshness) → phát hiện mâu thuẫn → tổng hợp câu trả lời cụ thể + link nguồn gốc. Giải quyết cả hai pain: trả lời thẳng VÀ không để học viên nhầm thông báo cũ.

## §3. Giải pháp tương tự đã nghiên cứu
- [MEE6 / Carl-bot FAQ Module]: flow = lưu câu hỏi–đáp cứng trong database → match keyword → trả lời. Đáng học: Trả lời thẳng, không redirect. Đáng né: Cứng, phải cập nhật thủ công mỗi lần thông báo thay đổi — không xử lý được mâu thuẫn. Mình khác gì: Tự động truy xuất từ kênh thông báo live, không cần cập nhật thủ công, có lớp scoring + conflict detection.
- [Notion AI / Guru]: flow = đặt câu hỏi → AI tìm trong knowledge base → trả lời kèm trích dẫn. Đáng học: Trả lời có trích dẫn nguồn cụ thể, không hallucinate. Đáng né: Chỉ hoạt động với nội dung đã được index trước — không live. Mình khác gì: Truy xuất live từ Discord channel history + xử lý mâu thuẫn giữa các bản thông báo khác ngày.

## §4. Thiết kế
- Lát cắt MỘT CÂU: Học viên K4 nhắn `/ask Khóa 4 nộp Gate 1 khi nào?` trong Discord → bot truy xuất `#thong-bao`, chọn thông báo Gate 1 K4 mới nhất, phát hiện thông báo cũ đã bị supersede, trả về embed: **"Deadline Gate 1 K4: 23:59 ngày 02/08/2026 · [🔗 Link thông báo gốc] · Thông báo cũ ngày 28/07 đã bị thay thế"** — không redirect, không bảo tự đọc.
- Non-goals (≥3 thứ KHÔNG build):
  1. Không trả lời câu hỏi chuyên môn kỹ thuật (code, thuật toán) — chỉ xử lý logistics.
  2. Không tự động đăng thông báo hoặc sửa thông báo trong kênh.
  3. Không crawl các kênh ngoài danh sách nguồn chính thức đã định nghĩa.
- Mức prototype nhắm tới: [ ] Sketch [ ] Mock [x] Working — Phần mock: `data/mock_messages.json` thay thế live Discord API. Phần thật: Pipeline 8 bước scoring + conflict detection + DeepSeek LLM synthesis chạy thật.
- Automation: [ ] augment [x] conditional [ ] automate — Lý do theo cost-of-error: Bot chỉ tự trả lời khi confidence ≥ 60 (VERIFIED/CONFLICT_RESOLVED). Khi không đủ bằng chứng → từ chối có cấu trúc + đưa nút "Chuyển Mod", không tự suy đoán. Cost of error khi trả lời sai deadline = học viên nộp bài sai giờ, hậu quả trực tiếp.
- §4b. Nguyên tắc đã áp dụng (HAX/PAIR):
  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|
  | G1 — Làm rõ hệ thống làm được gì | Embed hiển thị rõ "Thông tin đã xác minh từ #thong-bao" — không giả vờ biết tất cả. |
  | G2 — Làm rõ làm tốt đến đâu | Hiện confidence score (High/Medium) và nút "Xem cách xác minh" kèm score breakdown. |
  | G8 — Dễ dàng bác bỏ | Nút "Chuyển Mod" luôn hiển thị để học viên escalate khi không tin bot. |
  | G11 — Giải thích vì sao | Khi có conflict: "Thông báo cũ ngày 28/07 bị loại VÌ đã bị thông báo ngày 01/08 thay thế." |
  | PAIR - Errors & Graceful Failure | Khi confidence < 60: từ chối rõ ràng "Bot sẽ không suy đoán khi chưa có bằng chứng" + đưa nút Chuyển Mod. |

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8)
| Tình huống cụ thể | Lớp | Hành vi mong muốn | Nguyên tắc áp (G../PAIR) |
|---|---|---|---|
| 1. Có 2 thông báo Gate 1 K4 khác ngày — bot chọn thông báo cũ. | ① Nguồn sự thật | Scoring freshness + status phát hiện cái mới hơn; loại cái cũ kèm lý do "Thông báo cũ đã được cập nhật". | G11 (Giải thích vì sao) |
| 2. Bot trích dẫn nội dung không tồn tại trong thông báo (hallucination). | ① Nguồn sự thật | LLM chỉ được synthesize từ `source_content` đã truy xuất — prompt cấm suy đoán ngoài văn bản nguồn. | G2 (Độ chắc chắn) |
| 3. Học viên hỏi "tối nay có gì?" — mơ hồ, có thể là lịch học hoặc workshop. | ② Mơ hồ | Entity extractor trích `date_reference = "tối nay"`, LLM fallback phân tích intent; nếu vẫn unclear → trả INSUFFICIENT_EVIDENCE. | G10 (Thu hẹp phạm vi) |
| 4. Câu hỏi không có entity rõ ràng: "deadline là khi nào?" không có cohort. | ② Mơ hồ | Scoring cohort: ưu tiên thông báo "ALL", nếu không có → confidence thấp, hỏi lại hoặc Mod. | PAIR (Mental Model) |
| 5. Học viên hỏi về bài tập kỹ thuật: "hàm A viết thế nào?". | ③ Ngoài thẩm quyền | Intent classifier trả `unknown`, bot trả INSUFFICIENT_EVIDENCE, gợi ý hỏi kênh #chuyen-mon. | G1 (Phạm vi) |
| 6. Học viên hỏi thông tin của cohort khác (K3) trong khi đang là K4. | ③ Ngoài thẩm quyền | Cohort scoring penalty (-50) cho thông báo sai cohort; nếu không có thông báo K4 → INSUFFICIENT_EVIDENCE + Mod. | G10 |
| 7. Thông báo trong `#thong-bao` dùng từ viết tắt nội bộ bot chưa biết (vd "nộp OD"). | ④ Đặc thù domain | LLM synthesize từ văn bản nguồn nguyên văn, không cố diễn giải viết tắt — trả nguyên câu từ thông báo gốc kèm link. | PAIR (Errors) |
| 8. Có 2 kênh cùng đăng thông báo Gate 1 nhưng nội dung khác nhau (conflict thật). | ④ Đặc thù domain | Status VERIFIED_WITH_CONFLICT_RESOLVED: chọn nguồn authority cao hơn (official > mod), liệt kê nguồn bị loại + lý do. | G11, G2 |

## §6. Bốn đường đi của trải nghiệm
- Happy path (VERIFIED): Học viên hỏi "Workshop tối nay mấy giờ?" → intent=schedule, entity=tối nay/Workshop → retrieve msg_004 (score 87) → VERIFIED → embed xanh: "Workshop tối nay 20:00 · [🔗 Link]".
- Low-confidence (VERIFIED, medium): Học viên hỏi mơ hồ, chỉ 1 thông báo liên quan, score 65 → trả lời kèm badge "Medium confidence — Bấm Xem cách xác minh để kiểm tra".
- Conflict resolved (VERIFIED_WITH_CONFLICT_RESOLVED): "Khóa 4 nộp Gate 1 khi nào?" → phát hiện msg_001 (cũ, superseded) và msg_002 (mới, score 87) → embed xanh dương: deadline mới + "Thông báo cũ ngày 28/07 bị loại: đã được cập nhật".
- Không đủ bằng chứng (INSUFFICIENT_EVIDENCE): "Tuần sau có workshop đặc biệt không?" → không có thông báo khớp → embed đỏ: "Bot không tự suy đoán khi chưa có bằng chứng" + nút Chuyển Mod.

## §7. Kiểm thử & Chuẩn đạt chất lượng (Quality Bar)
- **Chuẩn đạt cam kết trước khi đo (Quality Bar):**
  1. **Con số tổng thể:** ≥ 80.0% câu thử đạt trên toàn bộ Golden Set (34 câu).
  2. **Điều KHÔNG cho phép sai lần nào (Zero-Tolerance):** Không được trả lời sai Deadline nộp bài lần nào (0% sai deadline) và 0% Bịa đặt thông tin (Zero Hallucination).
- **Lý do có điều thứ hai:** Sai deadline hoặc sai link nộp bài gây hậu quả trực tiếp khiến học viên mất điểm, trễ hạn nộp Gate, bị loại khỏi Hackathon mà người dùng không thể tự phát hiện trước khi quá muộn.
- **Bộ Golden Set (34 câu):** 22 câu đánh giá tổng quan (4 lớp chỗ khó) + 12 câu khiếm khuyết thực tế từ Discord log, khảo sát nguyên văn và tình huống tự test. File: `eval_dataset_22_questions.md` & `eval_12_flawed_questions.md`.
- **Kết quả đo lường thực tế:**
  - **Tỷ lệ tổng thể:** 79.4% (27/34 câu đạt) — Chênh lệch nhẹ `-0.6%` so với cam kết 80.0%.
  - **Độ chính xác Deadline:** 100% ĐẠT (0% lỗi deadline, chọn đúng 15:00 ngày 30/07/2026 cho Gate 1 K4).
  - **Độ trung thực nguồn:** 100% ĐẠT (0% bịa đặt thông tin).
- **Phân tích khoảng cách (Gap Analysis `-0.6%` cho Slide Demo):**
  - Chưa có dictionary từ viết tắt nội bộ (`OD` = Operational Document) làm tụt 2 case score.
  - Query phàn nàn dài gây nhiễu từ khóa matching.
  - Ngưỡng PAIR Guardrail 60.0 chặn an toàn các câu hỏi ghép 2 ý.

## §8. Phân công & kế hoạch
- Phân công có tên:
  - Trần Đăng Bách (2A202601266): Viết code pipeline (scoring, conflict, LLM), thử nghiệm Prompt, mock data, chuẩn bị Demo, trình bày.
  - Nguyễn Phi Hoàng (2A202601818): Xây dựng bộ Golden set, chạy đo lường, Validation, ghi kết quả §7.
  - Nguyễn Trọng Đức (2A202601636): Viết Spec, Evidence, thiết kế test cases mẫu cho Golden set (§7), định nghĩa quality bar, phối hợp willing users CP5.
- Willing users (≥3 tên): (Học viên K4) Bách, (Học viên K4) Hoàng, (Học viên K4) Đức. Kế hoạch CP5: Nhờ 3 học viên này thử 5 câu hỏi logistics thật trong Discord, đo time-to-answer và ghi nhận câu trả lời đúng/sai.
- Multi-prototype: Trục khác biệt: Mock JSON data vs. Live Discord API. Chọn: Mock JSON (CP2), vì Live API cần bot token và quyền truy cập kênh — stable hơn cho demo hackathon. CP3 roadmap: Live ingestion.

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
|---|---|---|
| CP2 — Giai đoạn 1 | **Xây dựng mock dataset từ chatlog thực của "Trợ lý Kute"** (`data/mock_messages.json`, ~200 entries `log_doc_xxx`). | Mining chatlog Discord thật cho thấy bot Trợ lý Kute hay redirect bảo tự đọc, hoặc trả lời suy đoán không có nguồn — đây là evidence trực tiếp cho pain point. Dữ liệu này trở thành bộ đối chiếu để test precision của pipeline. |
| CP2 — Giai đoạn 1 | **Thiết kế 4 thông báo "chính thức" mẫu** (`msg_001`→`msg_004`) để kiểm thử 3 case bắt buộc: conflict resolution (Gate 1 K4 có 2 thông báo mâu thuẫn), single verified (Workshop 20:00), insufficient evidence (Workshop đặc biệt tuần sau). | Cần bộ dữ liệu kiểm soát được để `test_end_to_end.py` có kết quả xác định. |
| CP2 — Giai đoạn 2 | **Chọn rule-based intent classifier** (`core/intent_classifier.py`) thay vì dùng LLM ngay từ đầu. 6 intent: document, deadline, submission, schedule, workshop, regulation. | Cost của LLM cho mỗi query quá cao khi scale. Rule-based đủ cho 80%+ câu hỏi logistics đơn giản. LLM chỉ được gọi khi classifier trả về `unknown`. |
| CP2 — Giai đoạn 2 | **Thêm LLM fallback (DeepSeek V3)** trong `decision_engine.py` khi `intent == "unknown"` hoặc `topic is None`. Temperature = 0.1 (gần deterministic). Max_tokens = 512. | Câu hỏi mơ hồ hoặc viết tắt nội bộ (vd: "nộp OD ở đâu") không match keyword nào — LLM cần để trích xuất intent/topic/cohort chính xác hơn. |
| CP2 — Giai đoạn 2 | **Thiết kế 8-factor scoring engine** (`core/source_ranker.py`): Authority (max 40), Cohort match (max 25, penalty -50), Topic match (max 20, penalty -60), Date reference (max 15, penalty -60), Resource type (max 15, penalty -60), Freshness (15), Status (+25/+20/-40/-50), Relevance guardrail (-80). | Ban đầu chỉ có 3 factor (authority, topic, freshness) nhưng gây sai khi có nhiều thông báo cùng topic khác cohort. Thêm cohort penalty và relevance guardrail để chặn trường hợp bot chọn sai thông báo K2 cho học viên K4. |
| CP2 — Giai đoạn 2 | **Thêm hard cap score ≤ 55 cho `log_doc_` entries** khi query intent là `schedule/deadline/workshop` (`source_ranker.py` dòng 148–149). | Chatlog Trợ lý Kute (log_doc_xxx) hay bị pipeline chọn nhầm thay thông báo chính thức vì có keyword overlap cao (chứa nhiều từ như "deadline", "workshop"). Cap tại 55 < threshold 60 đảm bảo log_doc không bao giờ VERIFIED cho các query loại này. |
| CP2 — Giai đoạn 2 | **Chọn threshold INSUFFICIENT_EVIDENCE tại confidence < 60** (`decision_engine.py` dòng 85). | Thử nghiệm với threshold 50 thấy bot chọn nguồn sai cohort vì score 52–55 vẫn được VERIFIED. Nâng lên 60 loại được tất cả trường hợp sai cohort trong golden set. |
| CP2 — Giai đoạn 2 | **Implement conflict detection qua `supersedes_source_id` chain** (`core/conflict_detector.py`). Chỉ đánh conflict khi candidate score ≥ 60 hoặc có explicit supersedes link. Bỏ qua `log_doc_` entries trong conflict calculation. | Nếu tính conflict cho cả log_doc_, bot báo CONFLICT_RESOLVED ngay cả khi không có thông báo chính thức mâu thuẫn thật sự — dễ gây confusion cho học viên. |
| CP2 — Giai đoạn 3 | **Xây dựng 3 loại Discord UI views** (`bot/views.py`): `VerifiedResultView` (nút "Mở nguồn" + "Xem cách xác minh"), `ConflictResultView` (nút "Mở nguồn chính" + "Xem các nguồn đã loại"), `InsufficientResultView` (nút "Chuyển Mod" + "Xem nguồn đã tìm thấy"). | Thiết kế ban đầu chỉ có 1 loại view chung. Tách 3 loại riêng vì behavior người dùng khác nhau: case VERIFIED cần xem nguồn gốc; case CONFLICT cần xem tại sao thông báo cũ bị loại; case INSUFFICIENT cần escalate ngay. |
| CP2 — Giai đoạn 3 | **Nút "Chuyển Mod" post ticket thật vào `MOD_CHANNEL_ID`** (`bot/views.py` dòng 77–116). Button bị disabled sau khi bấm (chống bấm nhiều lần). | Yêu cầu từ spec HAX/PAIR G8: học viên phải có lối thoát rõ ràng khi bot không biết. Không để học viên bị kẹt với embed đỏ không có action tiếp theo. |
| CP2 — Giai đoạn 3 | **LLM synthesis prompt giới hạn ≤ 40 từ**, trả lời phải dựa 100% vào `source_content` được cung cấp — không suy đoán (`llm_client.py` dòng 79–83). | Pain point gốc: bot cũ trả lời dài. Giới hạn cứng ≤ 40 từ để đảm bảo thông tin cốt lõi (deadline, link) nằm ở câu đầu tiên của embed. |
| CP2 — Giai đoạn 3 | **Retriever strict origin filter**: chỉ nhận source từ official channel ID hoặc DB (`core/retriever.py` dòng 121–122). Strict gateway cho live announcement: phải có keyword overlap > 0 hoặc là general announcement query mới được đưa vào candidates. | Tránh trường hợp bot lấy bất kỳ thông báo nào trong kênh không chính thức để trả lời — vi phạm nguyên tắc Faithfulness. |
| CP2 — Giai đoạn 3 | **Thêm 60-second in-memory cache cho live Discord messages** (`core/retriever.py` dòng 27–29). | Discord API rate-limit 50 requests/giây. Mỗi `/ask` command fetch live messages sẽ bị throttle nếu nhiều học viên hỏi cùng lúc trong giờ cao điểm. Cache 60 giây là trade-off hợp lý: thông báo mới nhất đa phần không thay đổi trong vòng 1 phút. |
| CP2 — Hoàn thiện | **5 test scenarios bắt buộc** (`tests/test_end_to_end.py`): Scenario 1 (msg_001 superseded → msg_002 K4 VERIFIED_CONFLICT), Scenario 2 (msg_004 Workshop 20:00 VERIFIED), Scenario 3 (Workshop đặc biệt tuần sau INSUFFICIENT), Scenario 4 (Workshop 99 không tồn tại INSUFFICIENT), Scenario 5 (Gate 1 K2 expired INSUFFICIENT). | Đây là bộ golden set tối thiểu để validate pipeline trước khi demo. Scenario 1 và 5 là case phức tạp nhất vì liên quan cohort cross-check và supersedes chain. |
| 2026-07-30 | **Cập nhật spec §1–§9** sau khi hoàn thiện code CP2. Xác định pain point chính xác từ chatlog Trợ lý Kute thực: bot redirect bảo tự đọc thay vì tổng hợp câu trả lời. Quy mô: ~10.000 học viên K3 & K4. | Mining `log_doc_101+` từ mock_messages.json cho thấy pattern rõ ràng: bot cũ luôn trả lời "bạn có thể tham khảo tại #thong-bao" hoặc "mình không truy cập được trang web bên ngoài" — đây là baseline pain cần so sánh sau khi deploy Verified Navigator. |




