document.addEventListener('DOMContentLoaded', () => {
    // --- TAB SWITCHING ---
    const navItems = document.querySelectorAll('.nav-item');
    const tabContents = document.querySelectorAll('.tab-content');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetTab = item.getAttribute('data-tab');
            
            navItems.forEach(n => n.classList.remove('active'));
            tabContents.forEach(t => t.classList.remove('active'));
            
            item.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
            
            // Auto load tab data
            if (targetTab === 'tab-announcements') loadAnnouncements();
            if (targetTab === 'tab-benchmark') loadBenchmark();
        });
    });

    // --- SCENARIO QUICK CHIPS ---
    const chipBtns = document.querySelectorAll('.chip-btn');
    const queryInput = document.getElementById('user-query-input');
    const queryForm = document.getElementById('query-form');

    chipBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const queryText = btn.getAttribute('data-query');
            queryInput.value = queryText;
            submitQuery(queryText);
        });
    });

    queryForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const queryText = queryInput.value.trim();
        if (queryText) submitQuery(queryText);
    });

    // --- SUBMIT QUERY TO BOT ENGINE ---
    async function submitQuery(question) {
        const statusBadge = document.getElementById('embed-status-badge');
        const titleText = document.getElementById('embed-title-text');
        const descText = document.getElementById('embed-desc-text');
        const fieldsContainer = document.getElementById('embed-fields-container');
        const rejectedBox = document.getElementById('rejected-list-box');
        const borderColor = document.getElementById('embed-border-color');

        // Reset Pipeline UI & show loading
        resetPipelineSteps();
        highlightPipelineStep(1, "Phân tích Intent & Entity...");
        
        statusBadge.className = 'status-badge status-idle';
        statusBadge.textContent = 'Đang Xử Lý Pipeline...';
        titleText.textContent = `Hỏi: "${question}"`;
        descText.textContent = "Đang truy xuất thông báo từ kênh #thong-bao và chấm điểm nguồn...";
        fieldsContainer.innerHTML = '';
        rejectedBox.innerHTML = '<div class="empty-state">Đang rà soát...</div>';

        try {
            const resp = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            });

            const data = await resp.json();
            
            // Step 2 & 3
            highlightPipelineStep(2, "Đã truy xuất candidates từ official channels");
            highlightPipelineStep(3, `Chấm điểm 8 yếu tố (Top score: ${data.verification_details?.total_score || 0})`);

            // Step 4: Confidence Check
            if (data.status === 'INSUFFICIENT_EVIDENCE') {
                highlightPipelineStep(4, "Confidence < 60.0 — Kích hoạt Guardrail từ chối");
                statusBadge.className = 'status-badge status-insufficient';
                statusBadge.textContent = 'INSUFFICIENT_EVIDENCE (Đã Từ Chối)';
                borderColor.style.background = '#f43f5e';
                titleText.textContent = "❌ Chưa Có Bằng Chứng Chính Thức Đủ Tin Cậy";
                descText.textContent = data.answer || "Bot từ chối suy đoán khi chưa tìm thấy thông báo xác minh.";
                
                document.getElementById('btn-view-source').disabled = true;
                document.getElementById('btn-view-score').disabled = true;
            } else if (data.status === 'VERIFIED_WITH_CONFLICT_RESOLVED') {
                highlightPipelineStep(4, "Confidence ≥ 60.0 — Vượt qua gate");
                highlightPipelineStep(5, "Đã hủy bỏ thông báo cũ bị mâu thuẫn!");
                highlightPipelineStep(6, "LLM Synthesis hoàn tất (DeepSeek V3)");

                statusBadge.className = 'status-badge status-conflict';
                statusBadge.textContent = 'VERIFIED (Đã Xác Minh & Loại Bản Cũ)';
                borderColor.style.background = '#06b6d4';
                titleText.textContent = "✅ Thông Tin Đã Xác Minh";
                descText.textContent = data.answer;

                document.getElementById('btn-view-source').disabled = false;
                document.getElementById('btn-view-score').disabled = false;
            } else {
                highlightPipelineStep(4, "Confidence ≥ 60.0 — Vượt qua gate");
                highlightPipelineStep(5, "Không có mâu thuẫn");
                highlightPipelineStep(6, "LLM Synthesis hoàn tất");

                statusBadge.className = 'status-badge status-verified';
                statusBadge.textContent = 'VERIFIED (Thông Tin Xác Minh)';
                borderColor.style.background = '#10b981';
                titleText.textContent = "✅ Thông Tin Đã Xác Minh";
                descText.textContent = data.answer;

                document.getElementById('btn-view-source').disabled = false;
                document.getElementById('btn-view-score').disabled = false;
            }

            // Render Rejected Sources (Ultra-Clean UI: show clean state when verified)
            if (data.status === 'INSUFFICIENT_EVIDENCE' && data.rejected_sources && data.rejected_sources.length > 0) {
                rejectedBox.innerHTML = data.rejected_sources.map(r => `
                    <div class="rejected-item">
                        <div class="rej-title">❌ [${r.id}] (#${r.channel_name})</div>
                        <div class="rej-reason">${r.reason}</div>
                    </div>
                `).join('');
            } else {
                rejectedBox.innerHTML = '<div class="empty-state">✅ Đã tối ưu sạch & không hiển thị nguồn mâu thuẫn rác</div>';
            }

        } catch (err) {
            console.error(err);
            statusBadge.textContent = 'Lỗi Kết Nối';
            descText.textContent = "Không thể kết nối với động cơ DecisionEngine backend.";
        }
    }

    function resetPipelineSteps() {
        for (let i = 1; i <= 6; i++) {
            const step = document.getElementById(`step-${i}`);
            if (step) step.classList.remove('active');
        }
    }

    function highlightPipelineStep(stepNum, text) {
        const step = document.getElementById(`step-${stepNum}`);
        if (step) {
            step.classList.add('active');
            if (text) {
                const detail = document.getElementById(`step-${stepNum}-detail`);
                if (detail) detail.textContent = text;
            }
        }
    }

    // --- TAB 2: LOAD OFFICIAL ANNOUNCEMENTS ---
    async function loadAnnouncements() {
        const container = document.getElementById('announcement-items-container');
        try {
            const resp = await fetch('/api/announcements');
            const data = await resp.json();
            
            if (data.status === 'success' && data.announcements) {
                container.innerHTML = data.announcements.map(ann => `
                    <div class="glass-card announcement-item">
                        <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                            <span style="font-weight:700; color:var(--primary);">${ann.id} • ${ann.channel_name || '#thong-bao'}</span>
                            <span class="status-badge ${ann.status === 'superseded' ? 'status-insufficient' : 'status-verified'}">${ann.status || 'active'}</span>
                        </div>
                        <p style="font-size:13px; color:var(--text-main); margin-bottom:8px;">${ann.content}</p>
                        <div style="font-size:11px; color:var(--text-muted);">
                            <i class="fa-regular fa-clock"></i> ${ann.posted_at || 'Mới nhất'} | Role: ${ann.author_role || 'official'} | Cohort: ${ann.cohort || 'ALL'}
                        </div>
                    </div>
                `).join('');
            }
        } catch (e) {
            container.innerHTML = '<div class="empty-state">Không thể tải thông báo</div>';
        }
    }

    // Form Add Announcement
    const addForm = document.getElementById('add-announcement-form');
    if (addForm) {
        addForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const content = document.getElementById('ann-content').value.trim();
            const channel = document.getElementById('ann-channel').value;
            const cohort = document.getElementById('ann-cohort').value;

            if (!content) return;

            try {
                const resp = await fetch('/api/announcements/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content, channel, cohort })
                });

                const res = await resp.json();
                alert("Đã đăng thông báo mới thành công! Bây giờ bạn có thể quay lại tab Chat để thử câu hỏi và xem Conflict Resolution.");
                document.getElementById('ann-content').value = '';
                loadAnnouncements();
            } catch (e) {
                alert("Lỗi khi thêm thông báo");
            }
        });
    }

    // --- TAB 3: LOAD BENCHMARK 34 CASES ---
    async function loadBenchmark() {
        const tbody = document.getElementById('benchmark-table-body');
        try {
            const resp = await fetch('/api/benchmark');
            const data = await resp.json();

            if (data.status === 'success' && data.results) {
                renderBenchmarkRows(data.results);

                // Filter buttons
                const filterBtns = document.querySelectorAll('.filter-btn');
                filterBtns.forEach(btn => {
                    btn.addEventListener('click', () => {
                        filterBtns.forEach(f => f.classList.remove('active'));
                        btn.classList.add('active');
                        const filterVal = btn.getAttribute('data-filter');
                        
                        if (filterVal === 'all') {
                            renderBenchmarkRows(data.results);
                        } else if (filterVal === 'set1') {
                            renderBenchmarkRows(data.results.filter(r => r.group.includes('Bộ 1')));
                        } else if (filterVal === 'set2') {
                            renderBenchmarkRows(data.results.filter(r => r.group.includes('Bộ 2')));
                        } else if (filterVal === 'set3') {
                            renderBenchmarkRows(data.results.filter(r => r.group.includes('Bộ 3')));
                        } else if (filterVal === 'set4') {
                            renderBenchmarkRows(data.results.filter(r => r.group.includes('Bộ 4')));
                        }
                    });
                });
            }
        } catch (e) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Không thể tải dữ liệu Benchmark</td></tr>';
        }
    }

    function renderBenchmarkRows(list) {
        const tbody = document.getElementById('benchmark-table-body');
        tbody.innerHTML = list.map(r => `
            <tr>
                <td><strong>#${r.id}</strong></td>
                <td><span style="font-size:11px; color:var(--accent-cyan); font-weight:600;">${r.group}</span></td>
                <td style="max-width:320px; font-weight:500;">"${r.question}"</td>
                <td><span class="status-badge ${r.status.includes('CONFLICT') ? 'status-conflict' : (r.status.includes('INSUFFICIENT') ? 'status-insufficient' : 'status-verified')}">${r.status}</span></td>
                <td><strong>${(r.confidence * 100).toFixed(0)}%</strong></td>
                <td>
                    ${r.is_passed 
                        ? '<span style="color:var(--accent-emerald); font-weight:700;"><i class="fa-solid fa-circle-check"></i> ĐẠT</span>' 
                        : '<span style="color:var(--accent-rose); font-weight:700;"><i class="fa-solid fa-circle-xmark"></i> CHƯA ĐẠT</span>'
                    }
                </td>
            </tr>
        `).join('');
    }
});
