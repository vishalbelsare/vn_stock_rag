# 📈 Trợ lý Phân tích Đầu tư AI cho Thị trường Chứng khoán Việt Nam

Dự án này là một ứng dụng web mạnh mẽ, sử dụng một đội ngũ AI Agents (được xây dựng bằng `crewAI`) để thực hiện quy trình phân tích cổ phiếu một cách tự động và đa chiều, đặc thù cho thị trường Việt Nam.

Lấy cảm hứng từ các mô hình **RAG (Retrieval-Augmented Generation)** tiên tiến, hệ thống này không chỉ dựa vào kiến thức có sẵn mà còn chủ động "truy xuất" thông tin thời gian thực từ nhiều nguồn khác nhau để đưa ra những phân tích sâu sắc và đáng tin cậy.

## ✨ Các tính năng chính

- **Hiểu ý định thông minh:** Sử dụng Mistral AI để phân tích yêu cầu của người dùng, tự động nhận diện tác vụ cần thực hiện (phân tích cổ phiếu, phân tích báo cáo tài chính, hoặc cả hai).
- **Phân tích đa chiều (Multi-Aspect Analysis):**
  - **Phân tích Thị trường:** Tự động tìm kiếm và tóm tắt các tin tức vĩ mô, ngành có ảnh hưởng.
  - **Phân tích Kỹ thuật:** Lấy dữ liệu giá/khối lượng, tính toán các chỉ báo (RSI, MACD, SMA...) và xác định xu hướng.
  - **Phân tích Tài chính & Cạnh tranh:** Đánh giá sức khỏe tài chính của công ty và tự động tạo bảng so sánh với các đối thủ cạnh tranh trong ngành.
  - **Phân tích Báo cáo Tài chính (PDF):** Cho phép người dùng tải lên file PDF, hệ thống sẽ dùng OCR để trích xuất và tóm tắt các điểm chính.
- **Tổng hợp và Ra quyết định:** Một AI Agent "Chiến lược gia" sẽ tổng hợp tất cả các báo cáo trên, chấm điểm từng yếu tố và đưa ra khuyến nghị cuối cùng: **MUA, BÁN, hoặc GIỮ** kèm theo luận điểm đầu tư rõ ràng.

## 🛠️ Công nghệ sử dụng

- **Backend Framework:** [CrewAI](https://github.com/joaomdmoura/crewAI)
- **Mô hình Ngôn ngữ (LLMs):** Google Gemini (2.5 Flash & 2.5 Pro), Mistral AI
- **Giao diện Người dùng (UI):** [Streamlit](https://streamlit.io/) & Streamlit-Chat
- **Nguồn dữ liệu:**
  - [vnstock](https://github.com/thinh-vu/vnstock) (Dữ liệu tài chính & kỹ thuật)
  - [Serper API](https://serper.dev/) (Tìm kiếm tin tức)
  - [Mistral OCR](https://mistral.ai/) (Đọc file PDF)
- **Ngôn ngữ:** Python

## 🚀 Hướng dẫn Cài đặt và Chạy dự án

### 1. Yêu cầu tiên quyết

- Python 3.12+
- Một tài khoản Google với API Key cho Gemini.
- Một tài khoản Mistral AI với API Key.
- Một tài khoản Serper.dev với API Key.

### 2. Cài đặt

**a. Clone repository này về máy:**
```bash
git clone https://github.com/meth04/vn_stock_rag.git
cd vn_stock_rag
```

**b. Tạo và kích hoạt môi trường ảo (khuyến khích):**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

**c. Cài đặt các thư viện cần thiết:**
```bash
pip install -r requirements.txt
```

**d. Thiết lập API Keys:**
Tạo một file có tên là `.env` trong thư mục gốc của dự án và điền các API key của bạn vào:```env
MISTRAL_API_KEY="your_mistral_api_key"
SERPER_API_KEY="your_serper_api_key"
GOOGLE_API_KEY="your_google_gemini_api_key"

# (Tùy chọn, cần thiết cho Windows) Thêm 2 dòng sau để sửa lỗi kết nối SSL
# Hãy đảm bảo đường dẫn đến môi trường ảo của bạn là chính xác
SSL_CERT_FILE="path/to/your/venv/Lib/site-packages/certifi/cacert.pem"
REQUESTS_CA_BUNDLE="path/to/your/venv/Lib/site-packages/certifi/cacert.pem"
```

### 3. Chạy ứng dụng

Sau khi cài đặt hoàn tất, mở Terminal và chạy lệnh sau:
```bash
streamlit run app.py
```
Một tab mới sẽ tự động mở ra trên trình duyệt của bạn. Bây giờ bạn đã có thể bắt đầu sử dụng Trợ lý Phân tích Đầu tư AI!

## 💡 Luồng hoạt động

1.  **Nhận yêu cầu:** Người dùng nhập câu lệnh và/hoặc tải file PDF lên giao diện.
2.  **Phân tích yêu cầu:** `main.py` sử dụng Mistral AI để xác định ý định của người dùng (chỉ phân tích cổ phiếu, chỉ phân tích PDF, hay phân tích toàn diện).
3.  **Khởi tạo Crew:** Dựa trên ý định, một "Crew" (đội ngũ) gồm các AI Agent phù hợp được tập hợp.
4.  **Thực thi Tasks:**
    -   `Market Data Analyst` tìm kiếm tin tức và phân tích kỹ thuật.
    -   `Financial Analyst` phân tích file PDF và gọi "siêu tool" để lấy dữ liệu tài chính & cạnh tranh.
5.  **Tổng hợp & Báo cáo:** `Investment Strategist` nhận tất cả các kết quả, tổng hợp, chấm điểm và viết ra báo cáo đầu tư cuối cùng, sau đó hiển thị lên giao diện.

## 🔮 Hướng phát triển trong tương lai

- [ ] Tích hợp biểu đồ tương tác vào báo cáo.
- [ ] Mở rộng khả năng phân tích tâm lý thị trường từ mạng xã hội.
- [ ] Xây dựng hệ thống quản lý người dùng và lưu trữ lịch sử phân tích.
