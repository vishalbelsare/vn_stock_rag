# 📈 Trợ lý Phân tích Chứng khoán AI Toàn diện cho Thị trường Việt Nam

Dự án này là một nền tảng phân tích đầu tư mạnh mẽ, sử dụng một đội ngũ AI Agents (xây dựng bằng `crewAI`) để tự động hóa hoàn toàn quy trình phân tích cổ phiếu đa chiều, đặc thù cho thị trường Việt Nam.

Một chatbot tương tác và một luồng dịch vụ tự động, gửi báo cáo phân tích chuyên nghiệp đến người dùng qua email hàng ngày.

<!-- ![Giao diện Chatbot](https://raw.githubusercontent.com/meth04/vn_stock_rag/main/assets/demo.png) -->

## ✨ Các tính năng chính

- **Hiểu Ngôn ngữ Tự nhiên:** Sử dụng **Google Gemini** để phân tích yêu cầu của người dùng, tự động nhận diện tác vụ cần thực hiện (phân tích cổ phiếu, tóm tắt báo cáo tài chính, hoặc phân tích toàn diện).
- **Phân tích Đa chiều & Trực quan:**
  - **Phân tích Vĩ mô & Ngành:** Tự động tìm kiếm, tổng hợp các tin tức vĩ mô, chính sách có ảnh hưởng đến thị trường.
  - **Phân tích Kỹ thuật Trực quan:** Tự động tạo và nhúng **biểu đồ nến (candlestick)** 12 tháng (kèm SMA20, SMA50) vào báo cáo, cùng với phân tích chi tiết về xu hướng, chỉ báo (RSI, MACD) và các ngưỡng hỗ trợ/kháng cự.
  - **Phân tích Cơ bản & Cạnh tranh:** Đánh giá sức khỏe tài chính (ROE), tự động tìm và tạo bảng so sánh với các đối thủ cạnh tranh trong ngành.
  - **Phân tích Báo cáo Tài chính (PDF):** Cho phép người dùng tải lên file PDF, hệ thống sử dụng **Gemini 1.5 Pro** để OCR và tóm tắt các điểm chính, tự động lưu cache để tối ưu cho các lần phân tích sau.
- **Tổng hợp & Đưa ra Khuyến nghị:** Một AI Agent "Tổng Biên tập" sẽ tổng hợp tất cả các báo cáo trên và đưa ra khuyến nghị cuối cùng: **MUA, BÁN, hoặc GIỮ** kèm theo luận điểm đầu tư rõ ràng.
- **Dịch vụ Bản tin Tự động (Daily Newsletter Service):**
  - **Lập lịch thông minh:** Một tiến trình chạy nền tự động kích hoạt vào 7 giờ sáng mỗi ngày.
  - **Tạo báo cáo hàng loạt:** Tự động phân tích tất cả các mã cổ phiếu được người dùng đăng ký.
  - **Xuất bản & Gửi Email:** Tự động chuyển đổi báo cáo phân tích (bao gồm cả biểu đồ) sang định dạng **PDF chuyên nghiệp** và gửi đến email của những người dùng tương ứng.

## 🛠️ Công nghệ sử dụng

- **Orchestration Framework:** [CrewAI](https://github.com/joaomdmoura/crewAI)
- **Mô hình Ngôn ngữ (LLMs):** **Google Gemini 2.5** (Pro & Flash)
- **Giao diện & Backend:** Flask & Flask-SocketIO
- **Triển khai & Môi trường:** **Docker & Docker Compose**
- **Nguồn dữ liệu:**
  - [vnstock](https://github.com/thinh-vu/vnstock) (Dữ liệu tài chính & kỹ thuật)
  - [Serper API](https://serper.dev/) (Tìm kiếm tin tức)
- **Công cụ phụ trợ:** Matplotlib & Mplfinance (Vẽ biểu đồ), PDFKit (Xuất PDF), SQLite (Quản lý đăng ký).
- **Ngôn ngữ:** Python 3.12+

## 🤖 Đội ngũ AI Agents

Hệ thống được vận hành bởi một đội ngũ gồm 5 AI Agents chuyên biệt, mỗi agent đảm nhận một nhiệm vụ riêng biệt:

- **1. Chuyên gia Phân tích Tin tức Thị trường:**
  - **Nhiệm vụ:** Hoạt động như một nhà báo kinh tế, liên tục tìm kiếm và tóm tắt những tin tức vĩ mô, chính sách của chính phủ, và các sự kiện ngành quan trọng nhất đang tác động đến toàn bộ thị trường.

- **2. Nhà phân tích Kỹ thuật (Chartist):**
  - **Nhiệm vụ:** Lấy dữ liệu giá và khối lượng, sau đó **vẽ biểu đồ nến (candlestick)** trực quan. Đồng thời, tính toán và diễn giải các chỉ báo kỹ thuật quan trọng như RSI, MACD, và các ngưỡng Hỗ trợ/Kháng cự.

- **3. Chuyên gia Phân tích Tài chính & Cạnh tranh:**
  - **Nhiệm vụ:** Một nhà phân tích tài chính doanh nghiệp. Nó sẽ "soi" sức khỏe của công ty mục tiêu qua các chỉ số như ROE và tự động tìm kiếm các đối thủ cạnh tranh chính để so sánh, giúp người dùng có cái nhìn toàn cảnh về vị thế của công ty trong ngành.

- **4. Chuyên gia Phân tích Báo cáo Tài chính (PDF):**
  - **Nhiệm vụ:**  Đọc hiểu file PDF. Khi người dùng tải lên một bản báo cáo tài chính, nó sẽ sử dụng công nghệ OCR của MistralOCR để "đọc" và chắt lọc những con số, thông tin cốt lõi về doanh thu, lợi nhuận, và dòng tiền.

- **5. Tổng biên tập Bản tin Chứng khoán:**
  - **Nhiệm vụ:** Agent này nhận tất cả các báo cáo riêng lẻ từ 4 chuyên gia trên và tổng hợp chúng lại thành một **Bản tin Chứng khoán duy nhất**, liền mạch và chuyên nghiệp. Đảm bảo cấu trúc báo cáo đúng chuẩn, văn phong hấp dẫn, và là người đưa ra khuyến nghị đầu tư cuối cùng (MUA, BÁN, hoặc GIỮ).


## 🚀 Hướng dẫn Cài đặt và Chạy (Khuyến khích dùng Docker)

Sử dụng Docker là cách dễ dàng và đáng tin cậy nhất để chạy dự án này mà không cần lo lắng về môi trường hay cài đặt thủ công các dependency phức tạp (như `wkhtmltopdf`).

### 1. Yêu cầu tiên quyết

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) đã được cài đặt.
- Một hoặc nhiều tài khoản Google với API Key cho Gemini. (Lý do nên có nhiều API key vì quá trình chạy agent tốn khá nhiều request)
- Một tài khoản Serper.dev với API Key.
- Một tài khoản Mistral với API Key cho MistralOCR.

### 2. Cài đặt và Chạy

**a. Clone repository:**
```bash
git clone https://github.com/meth04/vn_stock_rag.git
cd vn_stock_rag
```

**b. Thiết lập API Keys và Cấu hình:**
Tạo một file có tên là `.env`.
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```
Cấu hình file `env.`:

```bash
# API Keys
SERPER_API_KEY="your_serper_api_key"
GOOGLE_API_KEY_1="your_google_gemini_api_key_1"
GOOGLE_API_KEY_2="your_google_gemini_api_key_2"
# ...thêm bao nhiêu key tùy ý...
GOOGLE_API_KEY_6="your_google_gemini_api_key_6"
MISTRAL_API_KEY="your_mistral_api_key" # (Tùy chọn, nếu muốn dùng Mistral OCR)

# Cấu hình gửi Email (sử dụng Gmail và Mật khẩu Ứng dụng)
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=465
SENDER_EMAIL="your_email@gmail.com" # gmail của bạn
SMTP_PASSWORD="16chucai_matkhauungdung" # mật khẩu gmail app không phải mật khẩu gmail của bạn
```

**c. Khởi tạo Cơ sở dữ liệu (Chỉ chạy lần đầu):**
Khởi tạo database.
```bash
python database_manager.py
```

**d. Build và Run bằng Docker Compose:**
Mở Terminal trong thư mục gốc của dự án và chạy lệnh duy nhất:
```bash
docker-compose up --build
```
- Lần đầu tiên chạy, Docker sẽ build image, quá trình này có thể mất vài phút.
- Bạn sẽ thấy log từ cả hai dịch vụ (Web API và Scheduler) được in xen kẽ trong terminal.

### 3. Truy cập ứng dụng
- **Giao diện Chatbot:** Mở trình duyệt web và truy cập địa chỉ: `http://localhost:8000`
- **Tác vụ nền:** Dịch vụ Scheduler đang chạy âm thầm. Nó sẽ tự động phân tích và gửi email vào thời gian cố định trong ngày. 

### 4. Dừng ứng dụng
Trong terminal nơi bạn đã chạy `docker-compose up`, nhấn `Ctrl + C`. Để dọn dẹp hoàn toàn, chạy lệnh:
```bash
docker-compose down
```

## 🔮 Hướng phát triển trong tương lai

- [ ] Xây dựng giao diện cho người dùng tự đăng ký/hủy đăng ký nhận bản tin email.
- [ ] Tích hợp biểu đồ heatmap thị trường để cung cấp cái nhìn tổng quan hơn.
- [ ] Thêm nhiều loại báo cáo hơn (ví dụ: báo cáo ngành, báo cáo chiến lược).