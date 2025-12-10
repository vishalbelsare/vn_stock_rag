# VnStock Multi-Agent RAG: Hệ thống Phân tích Đầu tư Thông minh

> **Nền tảng phân tích chứng khoán chuyên sâu sử dụng kiến trúc Multi-Agent, tích hợp RAG (Retrieval-Augmented Generation) và Automation Pipeline.**

![Architecture Diagram](https://raw.githubusercontent.com/meth04/vn_stock_rag/main/assets/pipeline.png)

## 📖 Giới thiệu

**VnStock RAG** là giải pháp công nghệ tài chính (Fintech) tự động hóa quy trình nghiên cứu đầu tư. Thay vì phụ thuộc vào việc thu thập dữ liệu thủ công, hệ thống vận hành một tập hợp các **AI Agents** chuyên biệt, phối hợp để thực hiện:
1.  Thu thập dữ liệu thời gian thực (Real-time Data).
2.  Phân tích đa chiều (Vĩ mô, Kỹ thuật, Cơ bản).
3.  Xử lý tài liệu tài chính phức tạp (Financial Report OCR & RAG).
4.  Tổng hợp và xuất bản báo cáo khuyến nghị chuẩn mực.

Hệ thống bao gồm giao diện **Chatbot tương tác** và dịch vụ **Newsletter Automation** chạy nền (Background Scheduler).

---

## ✨ Tính năng Kỹ thuật Nổi bật

### 1. Xử lý Ngôn ngữ & Hiểu ý định người dùng (Intent Routing)
- Sử dụng **Google Gemini** làm bộ não trung tâm để phân loại ý định người dùng (Intent Classification).
- Tự động điều hướng yêu cầu: Chat hỏi đáp số liệu nhanh (RAG Query) hoặc Yêu cầu phân tích chuyên sâu (Full Analysis Workflow).

### 2. Phân tích Đa lớp (Multi-layered Analysis)
Hệ thống không chỉ tóm tắt văn bản mà thực hiện các tác vụ chuyên môn:
- **Market Intelligence:** Quét và lọc tin tức vĩ mô, chính sách tiền tệ tác động đến ngành.
- **Technical Analysis:** Tự động vẽ biểu đồ nến (Candlestick) tích hợp SMA20/50, tính toán RSI, MACD và xác định vùng kháng cự/hỗ trợ bằng Python (Matplotlib/Mplfinance).
- **Fundamental Analysis:** Truy xuất dữ liệu tài chính (P/E, P/B, ROE) và so sánh tương quan với nhóm đối thủ cạnh tranh (Peer Comparison).

### 3. RAG Engine cho Báo cáo Tài chính
- **Ingestion Pipeline:** Tích hợp **MistralOCR** để số hóa các file PDF báo cáo tài chính (dạng ảnh/scan).
- **Vector Store:** Lưu trữ dữ liệu vector để truy xuất chính xác các chỉ số tài chính phức tạp.
- **Context-aware:** Giảm thiểu ảo giác (Hallucination) bằng cách buộc model trích dẫn nguồn dữ liệu gốc.

### 4. Hệ thống Tự động hóa & Phân phối (Automation)
- **Scheduler:** Tiến trình chạy nền (Cron job) tự động kích hoạt phân tích danh mục theo dõi vào 07:00 sáng hàng ngày.
- **Reporting:** Tự động biên tập nội dung Markdown và render thành file PDF chuyên nghiệp.
- **Delivery:** Gửi email đính kèm báo cáo tới danh sách người dùng đăng ký.

---

## 🏗️ Kiến trúc Hệ thống (System Architecture)

Dự án được xây dựng trên nền tảng **CrewAI**, quản lý luồng làm việc của 5 Agents chuyên biệt:

| Agent (Tác nhân) | Vai trò & Nhiệm vụ Kỹ thuật |
| :--- | :--- |
| **Market Analyst** | Sử dụng `SerperDevTool` để thu thập tin tức, lọc nhiễu và đánh giá tác động vĩ mô (Sentiment Analysis). |
| **Technical Analyst** | Gọi API `Vnstock` lấy dữ liệu OHLCV, sử dụng `ChartingTool` để visualize dữ liệu và đưa ra tín hiệu kỹ thuật. |
| **Financial Competitor Analysis** | Tìm kiếm đối thủ cùng ngành và phân tích tin tức gần nhất sử dụng `SerperDevTool`. |
| **Financial Analyst** | Truy xuất BCTC, tìm kiếm các thông tin quan trọng (Doanh thu quý, Nợ ngắn hạn, Nợ phải trả,...)|
| **Report Editor** | Đóng vai trò Aggregator: Tổng hợp dữ liệu từ các luồng trên, kiểm tra tính nhất quán và biên soạn báo cáo cuối cùng. |

---

## 🧪 Kiểm soát Chất lượng (Evaluation Pipeline)

Khác với các dự án chatbot thông thường, VnStock RAG tích hợp quy trình đánh giá hiệu năng nghiêm ngặt (Evaluation-as-Code):

1.  **Component-wise Evaluation:** Đánh giá riêng lẻ từng Agent bằng phương pháp **LLM-as-a-Judge** với bộ tiêu chí (Rubrics) tùy chỉnh.
2.  **RAG Evaluation:** Sử dụng thư viện **Ragas** để đo lường các chỉ số:
    *   *Faithfulness:* Độ trung thực của câu trả lời so với dữ liệu gốc.
    *   *Context Recall:* Khả năng tìm kiếm thông tin trong tài liệu dài.
    *   *Answer Correctness:* Độ chính xác so với Ground Truth.
3.  **Monitoring Dashboard:** Tích hợp **Streamlit Dashboard** để trực quan hóa điểm số và truy vết lỗi (Debug) của hệ thống.

---

## 🛠️ Tech Stack

*   **Core Framework:** `CrewAI`, `LangChain`, `LlamaIndex`.
*   **LLM Provider:** Google Gemini (Flash 2.5 & Pro).
*   **Vector & Embedding:** Gemini Embeddings (`text-embedding-004`).
*   **OCR:** Mistral OCR.
*   **Backend API:** Flask, Flask-SocketIO (WebSocket).
*   **Data & Tools:** `vnstock`, `Serper`, `Matplotlib`, `PDFKit`.
*   **Database:** SQLite.
*   **Deployment:** Docker, Docker Compose.

---

## 🚀 Hướng dẫn Cài đặt & Triển khai

Khuyến khích sử dụng **Docker** để đảm bảo môi trường đồng nhất và tránh xung đột thư viện hệ thống (như `wkhtmltopdf`).

### 1. Yêu cầu tiên quyết
*   Docker Desktop đã được cài đặt.
*   API Keys: Google AI Studio (Gemini), Serper.dev, Mistral AI.

### 2. Cấu hình Môi trường
Clone repository và tạo file cấu hình:

```bash
git clone https://github.com/meth04/vn_stock_rag.git
cd vn_stock_rag
cp .env.example .env
```

Cập nhật các key trong file `.env`:
```ini
# AI Providers
GOOGLE_API_KEY_1="your_key"
GOOGLE_API_KEY_2="your_key"
# ... (Khuyến nghị dùng nhiều key để load balancing)
SERPER_API_KEY="your_key"
MISTRAL_API_KEY="your_key"

# Email Service (Gmail App Password)
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=465
SENDER_EMAIL="your_email@gmail.com"
SMTP_PASSWORD="your_app_password"
```

### 3. Chuẩn bị Dữ liệu
*   Tải thư mục `financial_reports` chứa các file PDF BCTC **[TẠI ĐÂY](https://drive.google.com/drive/folders/1NBpK8iOS33Ngv4Hs1I4QlV4ZJmaDy_uZ?usp=sharing)** và dán vào thư mục gốc.
*   Khởi tạo Database:
    ```bash
    python database_manager.py
    ```

### 4. Khởi chạy (Docker Compose)
Chạy lệnh sau để build và start toàn bộ dịch vụ:

```bash
docker-compose up --build
```

*Lưu ý: Quá trình build lần đầu có thể mất vài phút.*

### 5. Truy cập
*   **Web Interface:** `http://localhost:8000`
*   **Evaluation Dashboard (nếu chạy local):** `streamlit run dashboard.py`

---

## 🔮 Roadmap

- [x] Tích hợp RAG với OCR cho báo cáo tài chính.
- [ ] Phát triển giao diện quản lý danh mục đầu tư cá nhân hóa.
- [ ] Tích hợp thêm Model Open Source (Llama 3, Qwen) để chạy Local.

---

**Disclaimer:** *Hệ thống này là công cụ hỗ trợ phân tích, không phải là lời khuyên đầu tư tài chính. Người dùng chịu trách nhiệm với các quyết định giao dịch của mình.*