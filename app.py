# app.py

import streamlit as st
from streamlit_chat import message
import tempfile
import os
import base64
from main import run_analysis_workflow

# --- Cấu hình trang và CSS (Giữ nguyên và cải tiến) ---
st.set_page_config(page_title="Trợ lý Phân tích Đầu tư AI", layout="wide", page_icon="📈")

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

ICON_PATH = "assets/paperclip.svg"
if os.path.exists(ICON_PATH):
    icon_base64 = get_base64_of_bin_file(ICON_PATH)
    st.markdown(f"""
    <style>
        /* ... CSS giữ nguyên từ lần trước ... */
        /* Thanh nhập liệu cố định ở cuối */
        .input-container {{
            position: fixed; bottom: 0; left: 0; width: 100%;
            padding: 1rem 1rem; background-color: #0E1117;
            border-top: 1px solid #262730; display: flex;
            justify-content: center; align-items: center;
        }}
        /* Ô nhập text */
        .input-container .stTextInput {{
            position: relative; width: 60%; left: auto; bottom: auto;
        }}
        /* Nút upload file */
        .input-container .stFileUploader {{
            margin-left: 10px;
        }}
         .stFileUploader label {{ display: none; }}
        .stFileUploader div div button {{
            background-image: url("data:image/svg+xml;base64,{icon_base64}");
            background-repeat: no-repeat; background-size: 60%;
            background-position: center; width: 40px !important;
            height: 40px !important; border: none !important;
            border-radius: 50% !important; padding: 0 !important; margin: 0 !important;
        }}
        .stFileUploader div div button::before {{ content: "" !important; }}
    </style>
    """, unsafe_allow_html=True)
else:
    st.warning("Không tìm thấy file icon 'assets/paperclip.svg'. Nút upload file sẽ hiển thị mặc định.")


# --- Khởi tạo Session State ---
if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'uploaded_file_info' not in st.session_state:
    st.session_state['uploaded_file_info'] = None

# --- BẮT ĐẦU LOGIC MỚI: SỬ DỤNG CALLBACK ---

def handle_user_input():
    """
    Callback function để xử lý khi người dùng nhấn Enter.
    """
    user_input = st.session_state.user_input_widget
    if not user_input:
        return

    # 1. Thêm tin nhắn của người dùng vào lịch sử ngay lập tức
    st.session_state.history.append({"message": user_input, "is_user": True})
    
    # Chuẩn bị yêu cầu cuối cùng để gửi đến backend
    final_user_input = user_input
    file_info_for_prompt = ""
    if st.session_state.uploaded_file_info:
        file_path = st.session_state.uploaded_file_info['path']
        file_name = st.session_state.uploaded_file_info['name']
        final_user_input = f"{user_input} (sử dụng file báo cáo '{file_name}' tại '{file_path}')"
        file_info_for_prompt = f" (đính kèm file: *{file_name}*)"

    # 2. Thêm một placeholder "Thinking..." vào lịch sử
    st.session_state.history.append({"message": f"Đang phân tích yêu cầu của bạn{file_info_for_prompt}...", "is_user": False, "thinking": True})
    
    # Xóa file đính kèm khỏi state sau khi đã lấy thông tin
    st.session_state.uploaded_file_info = None

def handle_file_upload():
    """
    Callback function để xử lý khi người dùng tải file lên.
    """
    uploaded_file = st.session_state.file_uploader
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            tmpfile.write(uploaded_file.getvalue())
            temp_file_path = tmpfile.name
        st.session_state.uploaded_file_info = {"name": uploaded_file.name, "path": temp_file_path}

# --- Giao diện chính ---
st.title("Trợ lý Phân tích Đầu tư AI 📈")

# Hiển thị lịch sử chat
for i, msg_data in enumerate(st.session_state.history):
    is_user = msg_data.get("is_user", False)
    message(msg_data["message"], is_user=is_user, key=f"msg_{i}")

# --- Khu vực nhập liệu cố định với Callback ---
st.markdown('<div class="input-container">', unsafe_allow_html=True)
st.text_input(
    " ", placeholder="Nhập yêu cầu của bạn và nhấn Enter...", label_visibility="collapsed",
    key="user_input_widget", on_change=handle_user_input
)
st.file_uploader(
    " ", type=['pdf'], label_visibility="collapsed",
    key="file_uploader", on_change=handle_file_upload
)
st.markdown('</div>', unsafe_allow_html=True)


# --- LOGIC XỬ LÝ CHÍNH (CHẠY SAU KHI GIAO DIỆN ĐÃ ĐƯỢC VẼ) ---
# Kiểm tra xem có task "Thinking..." nào đang chờ không
last_message = st.session_state.history[-1] if st.session_state.history else None
if last_message and last_message.get("thinking"):
    
    # Lấy lại yêu cầu đầy đủ của người dùng từ tin nhắn trước đó
    full_user_request = st.session_state.history[-2]['message']
    
    final_input_for_backend = full_user_request
    # Kiểm tra lại xem có file nào được đính kèm trong state không (trường hợp này ít xảy ra nhưng để an toàn)
    if "(sử dụng file báo cáo tại" not in final_input_for_backend and st.session_state.uploaded_file_info:
         file_path = st.session_state.uploaded_file_info['path']
         final_input_for_backend = f"{full_user_request} (sử dụng file báo cáo tại '{file_path}')"

    # Chạy backend
    try:
        report_content, _ = run_analysis_workflow(final_input_for_backend)
        if not report_content:
             report_content = "Rất tiếc, đã có lỗi xảy ra trong quá trình phân tích. Vui lòng thử lại."
    except Exception as e:
        report_content = f"Đã xảy ra một lỗi nghiêm trọng: {e}"

    # Cập nhật tin nhắn "Thinking..." bằng kết quả thật
    st.session_state.history[-1] = {"message": report_content, "is_user": False}
    # Rerun để hiển thị kết quả cuối cùng
    st.rerun()