document.addEventListener('DOMContentLoaded', () => {
    const chatStream = document.getElementById('chat-stream');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chipBtns = document.querySelectorAll('.chip-btn');
    const tickerText = document.getElementById('ticker-text');

    // Quick Scenario Chips
    chipBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const queryText = btn.getAttribute('data-query');
            if (queryText) {
                chatInput.value = queryText;
                handleUserSubmit(queryText);
            }
        });
    });

    // Form Submit
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const queryText = chatInput.value.trim();
        if (queryText) {
            handleUserSubmit(queryText);
        }
    });

    async function handleUserSubmit(question) {
        // Clear input
        chatInput.value = '';

        // 1. Append User Message Bubble
        appendUserMessage(question);

        // 2. Scroll to bottom
        scrollToBottom();

        // 3. Update Pipeline Ticker Status
        updateTicker('<i class="fa-solid fa-spinner fa-spin"></i> Đang truy xuất 1,050 nguồn thông tin & kiểm tra mốc thời gian...');

        // 4. Create Thinking Bot Bubble
        const botBubble = appendThinkingMessage();
        scrollToBottom();

        try {
            const resp = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            });

            const data = await resp.json();

            // Update ticker
            if (data.status === 'INSUFFICIENT_EVIDENCE') {
                updateTicker('<i class="fa-solid fa-shield-virus" style="color:var(--accent-rose)"></i> Confidence < 60.0 — Kích hoạt Guardrail từ chối an toàn');
            } else if (data.status === 'VERIFIED_WITH_CONFLICT_RESOLVED') {
                updateTicker('<i class="fa-solid fa-circle-check" style="color:var(--accent-cyan)"></i> Đã xác minh & tự động loại bỏ thông báo cũ mâu thuẫn');
            } else {
                updateTicker('<i class="fa-solid fa-circle-check" style="color:var(--accent-emerald)"></i> Đã xác minh chính xác từ nguồn thông báo');
            }

            // Replace thinking bubble with verified embed
            renderBotEmbed(botBubble, data);
            scrollToBottom();

        } catch (err) {
            console.error(err);
            updateTicker('<i class="fa-solid fa-triangle-exclamation" style="color:var(--accent-rose)"></i> Lỗi kết nối máy chủ');
            botBubble.querySelector('.embed-description').textContent = 'Không thể kết nối với động cơ Verified Navigator. Vui lòng kiểm tra lại.';
        }
    }

    function appendUserMessage(text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'chat-message user-msg';
        msgDiv.innerHTML = `
            <div class="msg-avatar">
                <i class="fa-solid fa-user"></i>
            </div>
            <div class="msg-content">
                <div class="user-text-bubble">${escapeHtml(text)}</div>
            </div>
        `;
        chatStream.appendChild(msgDiv);
    }

    function appendThinkingMessage() {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'chat-message bot-msg';
        msgDiv.innerHTML = `
            <div class="msg-avatar">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="msg-content">
                <div class="msg-author">
                    <span class="author-name">Trợ Lý Navigator</span>
                    <span class="bot-tag">BOT</span>
                    <span class="msg-time">Đang xử lý...</span>
                </div>
                <div class="discord-embed">
                    <div class="embed-border" style="background:#6366f1;"></div>
                    <div class="embed-inner">
                        <h4 class="embed-title"><i class="fa-solid fa-spinner fa-spin"></i> Đang xác minh dữ liệu...</h4>
                        <div class="embed-description">Đang quét kho thông báo và chấm điểm nguồn chính thức...</div>
                    </div>
                </div>
            </div>
        `;
        chatStream.appendChild(msgDiv);
        return msgDiv;
    }

    function renderBotEmbed(msgDiv, data) {
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        msgDiv.querySelector('.msg-time').textContent = timeStr;

        const embedBorder = msgDiv.querySelector('.embed-border');
        const embedTitle = msgDiv.querySelector('.embed-title');
        const embedDesc = msgDiv.querySelector('.embed-description');

        if (data.status === 'INSUFFICIENT_EVIDENCE') {
            embedBorder.style.background = 'var(--accent-rose)';
            embedTitle.textContent = '⚠️ Chưa Đủ Bằng Chứng';
            embedDesc.textContent = data.answer || 'Hiện chưa tìm thấy thông báo hoặc tài liệu chính thức đủ tin cậy để trả lời câu hỏi này.';
        } else if (data.status === 'VERIFIED_WITH_CONFLICT_RESOLVED') {
            embedBorder.style.background = 'var(--accent-cyan)';
            embedTitle.textContent = '✅ Thông Tin Đã Xác Minh';
            embedDesc.textContent = data.answer;
        } else {
            embedBorder.style.background = 'var(--accent-emerald)';
            embedTitle.textContent = '✅ Thông Tin Đã Xác Minh';
            embedDesc.textContent = data.answer;
        }
    }

    function updateTicker(htmlContent) {
        tickerText.innerHTML = htmlContent;
    }

    function scrollToBottom() {
        chatStream.scrollTop = chatStream.scrollHeight;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
