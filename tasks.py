# tasks.py

from crewai import Task
from datetime import datetime

class StockAnalysisTasks():

    def market_news_analysis(self, agent):
        current_date_str = datetime.now().strftime('%d/%m/%Y')
        return Task(
            description=f"""
                Hôm nay là ngày: {current_date_str}.
                
                NHIỆM VỤ:
                Tìm kiếm và phân tích 3 tin tức vĩ mô hoặc sự kiện ngành nổi bật nhất có tác động trực tiếp đến thị trường chứng khoán Việt Nam trong 24h qua.
                
                YÊU CẦU CHI TIẾT:
                1. Không liệt kê tin rác, chỉ chọn tin có tác động lớn (Lãi suất, Tỷ giá, Chính sách công, Kết quả kinh doanh ngành).
                2. Với mỗi tin, phải có một câu "Đánh giá tác động": Tin này tích cực hay tiêu cực? Tại sao?
                3. Nếu không có tin nóng hôm nay, hãy lấy tin quan trọng nhất của 2 ngày gần nhất.

                Output format: Markdown (Gạch đầu dòng).
            """,
            expected_output="Báo cáo tóm tắt tin tức vĩ mô có nhận định tác động.",
            agent=agent,
            async_execution=True 
        )

    def technical_analysis(self, agent, symbol):
        return Task(
            description=f"""
                Thực hiện phân tích kỹ thuật chuyên sâu cho mã cổ phiếu '{symbol}'.
                
                QUY TRÌNH THỰC HIỆN:
                1. **Vẽ biểu đồ:** Dùng `ChartingTool` để tạo snapshot biểu đồ nến (1 năm). Bắt buộc phải lấy được đường dẫn ảnh.
                2. **Lấy chỉ số:** Dùng `TechDataTool` để lấy RSI, MACD, MA(50, 200).
                3. **Phân tích:**
                   - Xu hướng hiện tại là gì? (Uptrend, Downtrend, Sideway).
                   - Vị thế giá so với các đường MA.
                   - RSI đang ở vùng nào (Quá mua >70, Quá bán <30 hay Trung tính)?
                   - Xác định các vùng Hỗ trợ cứng và Kháng cự cứng (Ghi rõ con số cụ thể).
                
                YÊU CẦU OUTPUT (BẮT BUỘC):
                - Phải chứa dòng code hiển thị ảnh: `![Biểu đồ {symbol}](path/to/image.png)` (Lấy từ tool).
                - Nhận định: MUA, BÁN hay CHỜ MUA.
            """,
            expected_output=f"Báo cáo phân tích kỹ thuật chi tiết của {symbol} kèm biểu đồ minh họa.",
            agent=agent,
            async_execution=True 
        )

    def financial_competitor_analysis(self, agent, symbol):
        return Task(
            description=f"""
                Phân tích sức khỏe tài chính và tin tức đối thủ của '{symbol}'.
                
                QUY TRÌNH THỰC HIỆN (Làm từng bước):
                
                BƯỚC 1: XÁC ĐỊNH ĐỐI THỦ & LẤY SỐ LIỆU
                - Dùng `FinancialTool` để xác định danh sách đối thủ cùng ngành.
                - Chọn ra tối đa 3 đối thủ lớn nhất.
                - Lấy chỉ số P/E, P/B, ROE của {symbol} và 3 đối thủ này.

                BƯỚC 2: SĂN TIN ĐỐI THỦ (QUAN TRỌNG)
                - Với **MỖI** đối thủ trong 3 đối thủ trên, hãy dùng `SearchTool` thực hiện lệnh tìm kiếm riêng biệt.
                - Query mẫu: "Tin tức mới nhất về công ty [Tên đối thủ]".
                - **YÊU CẦU:** Lọc ra đúng **3 bài báo mới nhất/quan trọng nhất** cho từng đối thủ.
                
                YÊU CẦU OUTPUT (QUAN TRỌNG):
                1. **TUYỆT ĐỐI KHÔNG** bao quanh kết quả bằng dấu ```markdown hoặc ```. Chỉ trả về văn bản thô (Raw Markdown).
                2. Cấu trúc trả về:
                   - Phần 1: Nhận định chung về vị thế tài chính (Text).
                   - Phần 2: Mục "Chuyển động đối thủ" (Text).
                   - Phần 3: Bảng so sánh chỉ số tài chính (Table).
            """,
            expected_output=f"Báo cáo phân tích cạnh tranh {symbol} (Raw Markdown, không có code block).",
            agent=agent,
            async_execution=True 
        )

    def analyze_pdf_graph_rag(self, agent, ticker, extraction_query):
        return Task(
            description=f"Trích xuất chính xác số liệu từ tài liệu BCTC của {ticker} theo yêu cầu: {extraction_query}. Trả về nguyên văn con số tìm thấy.",
            expected_output="Dữ liệu thô trích xuất từ văn bản.",
            agent=agent,
            async_execution=True
        )

    def compose_newsletter(self, agent, context, symbol, chat_history=None, has_rag_data=False):
        
        rag_instruction = ""
        if has_rag_data:
            rag_instruction = """
            !!! ƯU TIÊN DỮ LIỆU NỘI BỘ (RAG) !!!
            Trong Context có phần "DỮ LIỆU TỪ BÁO CÁO TÀI CHÍNH GỐC". Đây là nguồn sự thật duy nhất (Single Source of Truth).
            Nếu số liệu từ RAG khác với số liệu từ Tool bên ngoài, HÃY DÙNG SỐ LIỆU TỪ RAG.
            """

        return Task(
            description=f"""
            Bạn là Tổng biên tập của FinAI. Nhiệm vụ của bạn là tổng hợp báo cáo phân tích cho mã **{symbol}**.

            {rag_instruction}

            ============== QUY TẮC "SẠCH SẼ" (CLEAN REPORTING) - CỰC KỲ QUAN TRỌNG ==============
            1. **XỬ LÝ BẢNG SỐ LIỆU (Table Cleaning):**
               - Kiểm tra bảng so sánh tài chính trong Context.
               - Nếu một dòng (ví dụ dòng P/E) toàn là "N/A" hoặc "0", **HÃY XÓA DÒNG ĐÓ KHỎI BẢNG**.
               - Nếu một cột (một đối thủ) toàn là "N/A", **HÃY XÓA CỘT ĐÓ**.
               - Tuyệt đối không để bảng hiển thị các ô "N/A" làm xấu báo cáo. Thà ít dữ liệu mà chất lượng còn hơn nhiều mà rỗng.
            
            2. **Đơn vị tiền tệ:**
               - Giá cổ phiếu: Viết **90,230 đồng**.
               - Doanh thu/Lợi nhuận/Nợ: Quy đổi về **Tỷ đồng**.
            
            3. **Không dùng Code Block:** Trả về Markdown thuần.
            ======================================================================================

            CẤU TRÚC BÁO CÁO (MARKDOWN):
            
            # 🇻🇳 BÁO CÁO PHÂN TÍCH: {symbol}
            *(Ngày: {datetime.now().strftime('%d/%m/%Y')})*

            ## 1. 📰 Điểm tin Vĩ mô & Ngành
            (Tóm tắt tin tức thị trường)

            ## 2. 🏢 Sức khỏe Tài chính & Vị thế
            - **Kết quả kinh doanh:** (Số liệu từ RAG/Tool).
            - **Định giá:** (Nhận định ngắn gọn về P/E, P/B nếu có số liệu).
            - **Chuyển động Đối thủ:** (Tin tức đối thủ).
            
            *(Chèn Bảng so sánh tài chính ĐÃ ĐƯỢC LÀM SẠCH vào cuối mục này)*

            ## 3. 📈 Góc nhìn Kỹ thuật
            - **Xu hướng & Chỉ báo.**
            - **Vùng giá quan trọng.**
            *(Chèn biểu đồ)*

            ## 4. 🎯 KẾT LUẬN & KHUYẾN NGHỊ
            - Khuyến nghị và Luận điểm.
            """,
            expected_output=f"Bản tin phân tích {symbol} chuyên nghiệp, bảng số liệu không chứa dòng N/A vô nghĩa.",
            agent=agent,
            context=context 
        )
