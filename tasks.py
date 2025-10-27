# tasks.py

from crewai import Task
from datetime import datetime

class StockAnalysisTasks():
    """
    Class chứa các task chuyên biệt cho việc tạo bản tin chứng khoán,
    tương ứng với kiến trúc 5 agent.
    """

    def market_news_analysis(self, agent):
        current_date_str = datetime.now().strftime('%d/%m/%Y')
        
        return Task(
            description=f"""
                Hôm nay là ngày {current_date_str}.
                Nhiệm vụ của bạn là phân tích tổng quan thị trường chứng khoán Việt Nam. 
                Hãy tìm và tóm tắt 2-3 tin tức vĩ mô, chính sách, hoặc sự kiện ngành quan trọng nhất ảnh hưởng đến thị trường trong phiên giao dịch gần đây nhất.
                QUAN TRỌNG: Nếu không tìm thấy tin tức chính xác cho ngày hôm nay, hãy tự động tìm kiếm cho ngày giao dịch gần nhất trước đó. Không được tự tạo ra kịch bản giả định.
            """,
            expected_output="Một đoạn văn hoàn chỉnh tóm tắt diễn biến và các tin tức vĩ mô quan trọng của phiên giao dịch gần nhất.",
            agent=agent,
        )

    def technical_analysis(self, agent, symbol):
        """Task cho Agent phân tích kỹ thuật."""
        return Task(
            description=f"Thực hiện phân tích kỹ thuật chi tiết cho chỉ số chứng khoán '{symbol}'. Sử dụng công cụ phân tích kỹ thuật để lấy dữ liệu và các chỉ báo cần thiết. Dựa vào kết quả, viết một nhận định chuyên sâu về xu hướng ngắn hạn và dài hạn, xác định các ngưỡng hỗ trợ và kháng cự quan trọng. Phân tích phải khách quan và dựa hoàn toàn vào dữ liệu kỹ thuật.",
            expected_output=f"Một báo cáo phân tích kỹ thuật hoàn chỉnh cho chỉ số {symbol}, bao gồm các mục: Nhận định xu hướng, Phân tích chỉ báo (RSI, MACD), và các Vùng giá quan trọng. Văn phong phải giống như mục 'Phân tích kỹ thuật' trong các bản tin chuyên nghiệp.",
            agent=agent,
            async_execution=False
        )

    def financial_competitor_analysis(self, agent, symbol):
        """Task cho Agent phân tích tài chính và đối thủ."""
        return Task(
            description=f"Sử dụng 'Công cụ Phân tích Tài chính và Cạnh tranh Toàn diện' với mã cổ phiếu '{symbol}'. Nhiệm vụ của bạn là thực thi công cụ này và trả về kết quả đầu ra của nó một cách chính xác. Không cần thêm bất kỳ phân tích hay bình luận nào khác.",
            expected_output=f"Kết quả đầu ra chính xác và đầy đủ từ tool, là một báo cáo Markdown chứa phân tích tài chính nội tại và bảng so sánh các chỉ số của {symbol} với các đối thủ.",
            agent=agent,
            async_execution=False
        )

    def analyze_pdf_report(self, agent, file_path):
        """Task cho Agent phân tích file PDF."""
        return Task(
            description=f"Phân tích chuyên sâu báo cáo tài chính từ file PDF được cung cấp tại đường dẫn: '{file_path}'. Sử dụng các công cụ cần thiết (OCR và đọc file) để trích xuất nội dung. Sau đó, tóm tắt những kết quả kinh doanh, điểm nhấn tài chính và các chỉ số quan trọng nhất được đề cập trong báo cáo.",
            expected_output="Một báo cáo markdown ngắn gọn, súc tích, tóm tắt các điểm nổi bật nhất từ file báo cáo tài chính PDF. Tập trung vào các con số về tăng trưởng doanh thu, lợi nhuận, biên lợi nhuận, và các điểm đáng chú ý về sức khỏe tài chính.",
            agent=agent,
            async_execution=False
        )

    def compose_newsletter(self, agent, context, symbol):
        """Task cuối cùng, dành cho Tổng biên tập (với prompt đã được gia cố)."""
        return Task(
            description=f"""
                Tổng hợp tất cả các báo cáo phân tích được cung cấp trong context để tạo ra một BẢN TIN CHỨNG KHOÁN hoàn chỉnh về cổ phiếu {symbol}.
                Nhiệm vụ của bạn là đóng vai một Tổng biên tập, tuân thủ NGHIÊM NGẶT cấu trúc được yêu cầu.

                Các báo cáo đầu vào bạn có trong context:
                1. Báo cáo Tổng quan Thị trường & Vĩ mô.
                2. Báo cáo Phân tích Kỹ thuật cho cổ phiếu '{symbol}'.
                3. Báo cáo Phân tích Cơ bản cho cổ phiếu '{symbol}'.
                4. Báo cáo Tóm tắt từ file PDF của '{symbol}'.

                **YÊU CẦU CẤU TRÚC CUỐI CÙNG (BẮT BUỘC TUÂN THỦ):**

                - **Tiêu đề chính:** BẢN TIN CHỨNG KHOÁN - Ngày {datetime.now().strftime('%d/%m/%Y')}
                
                - **Phần 1: TỔNG QUAN THỊ TRƯỜNG:**
                  Sử dụng **CHÍNH XÁC** nội dung từ Báo cáo Tổng quan Thị trường & Vĩ mô.
                
                - **Phần 2: PHÂN TÍCH DOANH NGHIỆP: {symbol}:**
                  Đây là phần trọng tâm. Bạn phải kết hợp thông minh thông tin từ 3 nguồn:
                  a. Báo cáo Phân tích Cơ bản ({symbol}).
                  b. Báo cáo Tóm tắt từ file PDF ({symbol}).
                  c. **Báo cáo Phân tích Kỹ thuật ({symbol}).**
                  
                  Hãy viết một phân tích tổng hợp về doanh nghiệp, bao gồm cả yếu tố cơ bản, kết quả kinh doanh từ PDF, và các tín hiệu kỹ thuật.
                
                - **Phần 3: KHUYẾN NGHỊ HÀNH ĐỘNG:**
                  Dựa trên TẤT CẢ thông tin đã tổng hợp ở trên, hãy đưa ra một khuyến nghị rõ ràng: **MUA**, **BÁN**, hoặc **GIỮ** cho cổ phiếu {symbol}. Kèm theo một đoạn giải thích ngắn gọn (2-3 câu) cho khuyến nghị đó.
            """,
            expected_output=f"Một file Markdown hoàn chỉnh, được định dạng đẹp mắt và tuân thủ nghiêm ngặt cấu trúc đã yêu cầu, tập trung vào cổ phiếu {symbol}.",
            agent=agent,
            context=context
        )