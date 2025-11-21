document.addEventListener('DOMContentLoaded', () => {
    const socket = io(window.location.origin);
    
    const elements = {
        welcomeScreen: document.getElementById('welcome-screen'),
        chatContainer: document.getElementById('chat-container'),
        userInput: document.getElementById('user-input'),
        sendButton: document.getElementById('send-btn'),
        uploadButton: document.getElementById('upload-btn'),
        fileInput: document.createElement('input'),
        filePreview: document.getElementById('file-preview'),
        chatHistoryList: document.getElementById('chat-history-list'),
        newChatBtn: document.getElementById('new-chat-btn'),
        // Modal Elements
        openSubModal: document.getElementById('open-sub-modal'),
        subModal: document.getElementById('sub-modal'),
        closeModal: document.querySelector('.close-modal'),
        confirmSub: document.getElementById('confirm-sub'),
        subEmail: document.getElementById('sub-email'),
        subTicker: document.getElementById('sub-ticker')
    };

    elements.fileInput.type = 'file';
    elements.fileInput.accept = '.pdf';

    let sessionId = localStorage.getItem('finai_session_id');
    let currentFilePath = null;
    let currentFileName = null;
    let isProcessing = false;
    
    // Biến theo dõi phần tử DOM của Thinking
    let currentBotMessageDiv = null;
    let currentThinkingSummary = null;
    let currentThinkingLogs = null;

    // --- SOCKET EVENTS ---
    socket.on('connect', () => { socket.emit('start_chat', { sessionId: sessionId }); });
    socket.on('session_initialized', (data) => {
        sessionId = data.sessionId;
        localStorage.setItem('finai_session_id', sessionId);
    });

    socket.on('load_sidebar_sessions', (data) => {
        elements.chatHistoryList.innerHTML = '';
        if (data.sessions.length === 0) {
            elements.chatHistoryList.innerHTML = '<div style="padding:10px;color:#aaa;text-align:center;font-size:0.8rem">Chưa có lịch sử</div>';
        }
        data.sessions.forEach(session => {
            const item = document.createElement('div');
            item.className = 'history-item';
            if (session.session_id === sessionId) item.classList.add('active');
            item.textContent = session.title || 'Đoạn chat mới';
            
            item.onclick = () => {
                if (session.session_id !== sessionId) {
                    document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
                    item.classList.add('active');
                    socket.emit('switch_session', { sessionId: session.session_id });
                }
            };
            elements.chatHistoryList.appendChild(item);
        });
    });

    socket.on('load_history', (data) => {
        elements.chatContainer.innerHTML = '';
        if (data.history.length > 0) {
            elements.welcomeScreen.classList.add('hidden');
            data.history.forEach(msg => appendMessage(msg.content, msg.role === 'user'));
        } else {
            elements.welcomeScreen.classList.remove('hidden');
        }
        scrollToBottom();
    });

    // --- LOGIC THINKING INLINE ---
    socket.on('thinking_step', (data) => {
        // Nếu chưa có tin nhắn bot, tạo mới ngay
        if (!currentBotMessageDiv) {
            createBotThinkingPlaceholder();
        }

        let cleanStep = data.step.replace(/^waiting\.\.\.\s*/, '').replace(/^\[.*?\]:\s*/, '');

        // Cập nhật text trên thanh Summary
        if (currentThinkingSummary) {
            currentThinkingSummary.innerHTML = `<span class="status-spinner"></span> ${cleanStep}`;
        }

        // Thêm log vào chi tiết
        if (currentThinkingLogs) {
            const logItem = document.createElement('div');
            logItem.textContent = "> " + cleanStep;
            currentThinkingLogs.appendChild(logItem);
            currentThinkingLogs.scrollTop = currentThinkingLogs.scrollHeight;
        }
    });

    socket.on('analysis_complete', (data) => {
        // Kết thúc thinking: đổi icon, đóng accordion
        if (currentThinkingSummary) {
            currentThinkingSummary.innerHTML = `<i class="fa-solid fa-check" style="color:green"></i> Đã hoàn thành`;
            // Tự động đóng
            const details = currentThinkingSummary.parentElement;
            if(details) details.removeAttribute('open');
        }

        // Append nội dung Markdown Report vào cùng message đó
        if (currentBotMessageDiv) {
            const contentDiv = currentBotMessageDiv.querySelector('.message-content');
            
            // Tạo một div mới cho report để nó nằm dưới thinking
            const reportDiv = document.createElement('div');
            reportDiv.className = 'markdown-body';
            reportDiv.style.marginTop = '15px'; // Cách phần thinking một chút
            reportDiv.innerHTML = marked.parse(data.report);
            
            contentDiv.appendChild(reportDiv);
        }

        resetInputState();
        scrollToBottom();
    });

    socket.on('analysis_error', (data) => {
        if (currentBotMessageDiv) {
            const contentDiv = currentBotMessageDiv.querySelector('.message-content');
            const errDiv = document.createElement('div');
            errDiv.style.color = 'red';
            errDiv.style.marginTop = '10px';
            errDiv.textContent = `Lỗi: ${data.error}`;
            contentDiv.appendChild(errDiv);
        }
        resetInputState();
    });

    // --- FUNCTIONS ---
    
    // Tạo cấu trúc: Message -> Content -> Thinking Accordion
    function createBotThinkingPlaceholder() {
        elements.welcomeScreen.classList.add('hidden');

        const msgDiv = document.createElement('div');
        msgDiv.className = 'message bot-message';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Cấu trúc Accordion
        contentDiv.innerHTML = `
            <div class="thinking-process">
                <details open>
                    <summary><span class="status-spinner"></span> Đang khởi động...</summary>
                    <div class="thinking-logs"></div>
                </details>
            </div>
        `;
        
        msgDiv.appendChild(contentDiv);
        elements.chatContainer.appendChild(msgDiv);
        scrollToBottom();

        // Lưu tham chiếu
        currentBotMessageDiv = msgDiv;
        currentThinkingSummary = contentDiv.querySelector('summary');
        currentThinkingLogs = contentDiv.querySelector('.thinking-logs');
    }

    function appendMessage(content, isUser) {
        elements.welcomeScreen.classList.add('hidden');
        
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content markdown-body';

        if (isUser) contentDiv.textContent = content;
        else contentDiv.innerHTML = marked.parse(content);

        msgDiv.appendChild(contentDiv);
        elements.chatContainer.appendChild(msgDiv);
    }

    function resetInputState() {
        isProcessing = false;
        currentBotMessageDiv = null;
        currentThinkingSummary = null;
        currentThinkingLogs = null;
        
        elements.sendButton.disabled = false;
        elements.userInput.disabled = false;
        elements.userInput.focus();
    }

    function scrollToBottom() {
        elements.chatContainer.scrollTo({ top: elements.chatContainer.scrollHeight, behavior: 'smooth' });
    }

    // --- HANDLERS ---
    async function handleSend() {
        const query = elements.userInput.value.trim();
        if ((!query && !currentFilePath) || isProcessing) return;

        isProcessing = true;
        elements.sendButton.disabled = true;
        elements.userInput.disabled = true;

        let displayQuery = query;
        if (currentFileName) displayQuery += `\n[File: ${currentFileName}]`;
        
        appendMessage(displayQuery, true);
        scrollToBottom();

        elements.userInput.value = '';
        elements.userInput.style.height = 'auto';
        elements.filePreview.classList.remove('active');
        
        // Socket emit sẽ trigger thinking_step -> createBotThinkingPlaceholder
        socket.emit('run_analysis', {
            query: query,
            file_info: currentFilePath ? { path: currentFilePath, name: currentFileName } : null
        });
        
        currentFilePath = null;
        currentFileName = null;
    }

    elements.sendButton.addEventListener('click', handleSend);
    elements.userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
    });
    elements.userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        elements.sendButton.disabled = (this.value.trim() === '' && !currentFilePath);
    });

    elements.uploadButton.addEventListener('click', () => elements.fileInput.click());
    elements.fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if(!file) return;
        const formData = new FormData(); formData.append('file', file);
        elements.filePreview.classList.add('active');
        elements.filePreview.innerHTML = 'Đang tải...';
        try {
            const res = await fetch('/uploadfile/', { method: 'POST', body: formData });
            const data = await res.json();
            if(data.file_path) {
                currentFilePath = data.file_path;
                currentFileName = data.file_name;
                elements.filePreview.innerHTML = `<i class="fa-solid fa-file-pdf"></i> ${data.file_name}`;
                elements.sendButton.disabled = false;
            }
        } catch(e) { elements.filePreview.innerHTML = 'Lỗi tải file'; }
        elements.fileInput.value = '';
    });

    elements.newChatBtn.addEventListener('click', () => {
        document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
        localStorage.removeItem('finai_session_id');
        location.reload();
    });

    // Modal Logic
    if (elements.openSubModal) elements.openSubModal.addEventListener('click', () => elements.subModal.classList.remove('hidden'));
    if (elements.closeModal) elements.closeModal.addEventListener('click', () => elements.subModal.classList.add('hidden'));
    window.addEventListener('click', (e) => { if (e.target === elements.subModal) elements.subModal.classList.add('hidden'); });

    elements.confirmSub.addEventListener('click', async () => {
        const email = elements.subEmail.value;
        const ticker = elements.subTicker.value;
        if(!email || !ticker) return alert('Vui lòng nhập đủ thông tin');
        
        elements.confirmSub.textContent = 'Đang xử lý...';
        try {
            await fetch('/subscribe', { 
                method: 'POST', headers: {'Content-Type':'application/json'}, 
                body: JSON.stringify({email, ticker})
            });
            alert('Đăng ký thành công!');
            elements.subModal.classList.add('hidden');
        } catch(e) { alert('Lỗi kết nối'); }
        elements.confirmSub.textContent = 'Xác nhận';
    });
});