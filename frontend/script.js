// frontend/script.js

document.addEventListener('DOMContentLoaded', () => {
    const socket = io(window.location.origin);

    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const uploadButton = document.getElementById('upload-button');
    const fileInput = document.getElementById('file-input');
    const fileInfoDiv = document.getElementById('file-info');

    let uploadedFilePath = null;
    let uploadedFileName = null;
    let isThinking = false;

    // --- Hàm trợ giúp ---
    function addMessage(content, isUser, isHtml = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', isUser ? 'user-message' : 'bot-message');
        
        if (isHtml) {
            messageDiv.innerHTML = content;
        } else {
            messageDiv.textContent = content;
        }
        
        chatContainer.appendChild(messageDiv);
        window.scrollTo(0, document.body.scrollHeight); // Luôn cuộn xuống cuối trang
        return messageDiv;
    }

    function createThinkingMessage() {
        const content = `
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <div class="spinner"></div>
                <span style="margin-left: 10px;">AI đang suy nghĩ...</span>
            </div>
            <pre id="live-log"></pre>
        `;
        return addMessage(content, false, true);
    }

    // --- Hàm xử lý chính ---
    const handleSendMessage = () => {
        const query = userInput.value.trim();
        if (!query || isThinking) return;

        isThinking = true;
        sendButton.disabled = true;
        uploadButton.disabled = true;

        addMessage(query, true);
        userInput.value = '';

        let fullQuery = query;
        if (uploadedFilePath) {
            fullQuery = `${query} (sử dụng file báo cáo '${uploadedFileName}' tại '${uploadedFilePath}')`;
        }
        
        const thinkingMessageElement = createThinkingMessage();
        
        console.log("Sending 'run_analysis' to backend.");
        socket.emit('run_analysis', { query: fullQuery });

        uploadedFilePath = null;
        uploadedFileName = null;
        fileInfoDiv.textContent = '';

        const logArea = thinkingMessageElement.querySelector('#live-log');

        const onLogUpdate = (data) => {
            logArea.textContent += data.log;
            logArea.scrollTop = logArea.scrollHeight;
        };

        const onAnalysisComplete = (data) => {
            // Sử dụng thư viện marked để chuyển đổi Markdown sang HTML
            const reportHtml = marked.parse(data.report);
            thinkingMessageElement.innerHTML = reportHtml;
            
            isThinking = false;
            sendButton.disabled = false;
            uploadButton.disabled = false;
            
            socket.off('log_update', onLogUpdate);
            socket.off('analysis_complete', onAnalysisComplete);
            socket.off('analysis_error', onAnalysisError);
        };

        const onAnalysisError = (data) => {
            thinkingMessageElement.innerHTML = `<strong style="color: red;">Lỗi:</strong><br>${data.error}`;
            
            isThinking = false;
            sendButton.disabled = false;
            uploadButton.disabled = false;

            socket.off('log_update', onLogUpdate);
            socket.off('analysis_complete', onAnalysisComplete);
            socket.off('analysis_error', onAnalysisError);
        };

        socket.on('log_update', onLogUpdate);
        socket.on('analysis_complete', onAnalysisComplete);
        socket.on('analysis_error', onAnalysisError);
    };

    // --- Gắn sự kiện ---
    sendButton.addEventListener('click', handleSendMessage);
    userInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); handleSendMessage(); } });
    uploadButton.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        fileInfoDiv.textContent = `Đang tải lên: ${file.name}...`;
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/uploadfile/', { method: 'POST', body: formData });
            const data = await response.json();
            if (data.file_path) {
                uploadedFilePath = data.file_path;
                uploadedFileName = data.file_name;
                fileInfoDiv.textContent = `✅ Đã đính kèm: ${data.file_name}`;
            } else {
                fileInfoDiv.textContent = `❌ Lỗi tải file: ${data.error}`;
            }
        } catch (error) {
            fileInfoDiv.textContent = '❌ Lỗi kết nối khi tải file.';
        }
        fileInput.value = '';
    });
});