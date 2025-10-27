# app.py

import streamlit as st
from streamlit_chat import message
import os
import base64
import tempfile
import sys
import io
from contextlib import contextmanager

# Import logic chính từ main.py (đảm bảo main.py của bạn là phiên bản ổn định)
from main import run_analysis_workflow

# --- Context Manager để bắt log (giống utils.py cũ) ---
@contextmanager
def st_capture(output_func):
    original_stdout = sys.stdout
    string_io = io.StringIO()
    sys.stdout = string_io
    try:
        yield
    finally:
        output = string_io.getvalue()
        sys.stdout = original_stdout
        output_func(output)

# --- Cấu hình trang ---
st.set_page_config(page_title="Trợ lý Phân tích AI", layout="wide", page_icon="📈")

# --- Hàm trợ giúp ---
@st.cache_data
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --- CSS & HTML cho giao diện ---
ICON_PATH = "assets/paperclip.svg"
if os.path.exists(ICON_PATH):
    icon_base64 = get_base64_of_bin_file(ICON_PATH)
else:
    icon_base64 = "" # Fallback

st.markdown(f"""
<style>
    /* ------------------- CÀI ĐẶT CHUNG ------------------- */
    /* Ẩn header, footer và menu mặc định của Streamlit */
    #MainMenu, header, footer {{
        visibility: hidden;
    }}
    /* Tùy chỉnh khu vực chính của ứng dụng */
    .main .block-container {{
        padding-top: 2rem;
        /* Thêm khoảng trống ở dưới cùng để thanh nhập liệu không che mất nội dung */
        padding-bottom: 8rem; 
    }}

    /* ------------------- BONG BÓNG CHAT ------------------- */
    /* Container cho mỗi tin nhắn */
    .stChatMessage {{
        border-radius: 18px;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid transparent;
        max-width: 80%;
        line-height: 1.5;
    }}

    /* Bong bóng chat của người dùng */
    .stChatMessage[data-testid="stChatMessageContent"] {{
        background-color: #007bff;
        color: white;
        align-self: flex-end; /* Đẩy sang phải */
        border-bottom-right-radius: 4px;
    }}

    /* Bong bóng chat của Bot */
    div[data-testid="stChatMessage"]:not(:has(div[data-testid="stChatMessageContent"])) {{
        background-color: #ffffff;
        color: #333;
        align-self: flex-start; /* Đẩy sang trái */
        border: 1px solid #e5e5e5;
        border-bottom-left-radius: 4px;
    }}
    
    /* Tùy chỉnh markdown bên trong bong bóng của bot */
    .bot-message-container h3 {{
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }}
    
    .bot-message-container table {{
        width: 100%;
        border-collapse: collapse;
    }}

    .bot-message-container th, .bot-message-container td {{
        border: 1px solid #ddd;
        padding: 8px;
    }}

    .bot-message-container th {{
        background-color: #f2f2f2;
    }}

    /* ------------------- THANH NHẬP LIỆU CỐ ĐỊNH ------------------- */
    /* Container chính bọc lấy thanh nhập liệu, cố định ở cuối trang */
    .st-emotion-cache-18ni7ap {{ 
        position: fixed;
        bottom: 0;
        left: 0; /* Đảm bảo nó căng hết chiều ngang */
        width: 100%;
        background-color: rgba(240, 242, 245, 0.8); /* Màu nền bán trong suốt */
        backdrop-filter: blur(10px); /* Hiệu ứng mờ */
        padding: 1rem 0;
        border-top: 1px solid #e0e0e0;
        z-index: 99; /* Đảm bảo nó luôn nổi lên trên */
    }}

    /* Căn giữa các thành phần bên trong thanh nhập liệu */
    .st-emotion-cache-18ni7ap > div {{
        display: flex;
        justify-content: center;
    }}

    /* Container phụ bọc nút upload và ô text */
    .st-emotion-cache-18ni7ap > div > div {{
        display: flex;
        align-items: center;
        width: 100%;
        max-width: 800px; /* Giới hạn chiều rộng tối đa */
        background-color: #ffffff;
        border: 1px solid #ccc;
        border-radius: 0.75rem; /* Bo tròn nhiều hơn */
        padding: 0.3rem 0.5rem;
    }}

    /* ------------------- NÚT UPLOAD FILE ------------------- */
    /* Ẩn label mặc định của nút upload */
    .stFileUploader label {{
        display: none;
    }}

    /* Tùy chỉnh nút bấm */
    .stFileUploader div[data-testid="stFileUploadDropzone"] button {{
        background-image: url("data:image/svg+xml;base64,{icon_base64}");
        background-repeat: no-repeat;
        background-size: 20px; /* Kích thước icon */
        background-position: center;
        width: 40px !important;
        height: 40px !important;
        border: none !important;
        border-radius: 50% !important;
        padding: 0 !important;
        margin: 0 5px 0 0 !important;
        background-color: transparent;
        transition: background-color 0.2s;
    }}
    
    /* Hiệu ứng khi di chuột qua */
    .stFileUploader div[data-testid="stFileUploadDropzone"] button:hover {{
        background-color: #f0f2f5;
    }}

    /* Ẩn icon mặc định của Streamlit */
    .stFileUploader div[data-testid="stFileUploadDropzone"] button::before {{
        content: "" !important;
    }}
    
    /* Ẩn danh sách file đã upload */
    .st-emotion-cache-1h9usn1 {{
        display: none;
    }}
    
    /* ------------------- Ô NHẬP TEXT ------------------- */
    .stTextInput {{
        flex-grow: 1; /* Cho phép ô input chiếm hết không gian còn lại */
    }}
    
</style>
""", unsafe_allow_html=True)

# --- Khởi tạo Session State ---
if "history" not in st.session_state:
    st.session_state.history = [{"message": "Chào bạn! Tôi là Trợ lý Phân tích Đầu tư. Hãy đặt câu hỏi hoặc đính kèm báo cáo tài chính để bắt đầu.", "is_user": False}]
if "uploaded_file_info" not in st.session_state:
    st.session_state.uploaded_file_info = None

# --- Giao diện chính ---
st.title("Trợ lý Phân tích Đầu tư AI 📈")

# Hiển thị lịch sử chat
for i, msg_data in enumerate(st.session_state.history):
    is_user = msg_data.get("is_user", False)
    if is_user:
        message(msg_data["message"], is_user=True, key=f"user_{i}")
    else:
        # Nếu là tin nhắn của bot, dùng markdown để hiển thị đẹp hơn
        st.markdown(f"<div class='bot-message-container'><strong>Trợ lý AI:</strong>{msg_data['message']}</div>", unsafe_allow_html=True)
        if "log" in msg_data:
             with st.expander("Xem quá trình suy nghĩ của AI", expanded=True):
                 st.code(msg_data["log"], language='text')

# --- Logic xử lý chính ---
def process_request():
    user_input = st.session_state.user_text_input
    if not user_input:
        return
        
    # Thêm tin nhắn của user vào lịch sử
    st.session_state.history.append({"message": user_input, "is_user": True})
    
    final_user_input = user_input
    if st.session_state.uploaded_file_info:
        file_path = st.session_state.uploaded_file_info['path']
        file_name = st.session_state.uploaded_file_info['name']
        final_user_input = f"{user_input} (sử dụng file báo cáo '{file_name}' tại '{file_path}')"
        st.info(f"Đang phân tích yêu cầu cùng với file: **{file_name}**")
        st.session_state.uploaded_file_info = None # Xóa file sau khi đã lấy thông tin

    # Thêm tin nhắn "Thinking..."
    thinking_message = "🤖 Các AI Agent đang hội ý, vui lòng chờ..."
    st.session_state.history.append({"message": thinking_message, "is_user": False, "log": ""})
    
    # Chạy backend và bắt log
    try:
        def update_log(new_log):
            st.session_state.history[-1]["log"] += new_log
        
        with st_capture(update_log):
            # Gọi hàm logic cốt lõi từ main.py
            report_content, _ = run_analysis_workflow(final_user_input)

        # Cập nhật tin nhắn cuối cùng bằng kết quả thật
        st.session_state.history[-1]["message"] = report_content

    except Exception as e:
        error_msg = f"Đã xảy ra lỗi nghiêm trọng: {e}"
        st.session_state.history[-1]["message"] = error_msg
        st.error(error_msg)

# --- Thanh nhập liệu cố định ở cuối trang ---
# Sử dụng st.container để nhóm các widget
footer = st.container()
with footer:
    cols = st.columns([1, 10]) # Cột cho nút upload và ô text
    with cols[0]:
        uploaded_file = st.file_uploader(
            "Upload", 
            type=['pdf'], 
            label_visibility="collapsed"
        )
        if uploaded_file:
             # Lưu file tạm và cập nhật state
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                tmpfile.write(uploaded_file.getvalue())
                temp_file_path = tmpfile.name
            st.session_state.uploaded_file_info = {"name": uploaded_file.name, "path": temp_file_path}
            st.info(f"Đã đính kèm: {uploaded_file.name}")

    with cols[1]:
        st.text_input(
            "Input",
            placeholder="Nhập yêu cầu của bạn và nhấn Enter...",
            label_visibility="collapsed",
            key="user_text_input",
            on_change=process_request
        )