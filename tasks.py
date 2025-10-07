# tasks.py

from crewai import Task
from datetime import datetime

class StockAnalysisTasks():
    """Class chứa các task đã được tối ưu."""
    def market_analysis(self, agent, symbol):
        """Task hợp nhất: Tin tức và Kỹ thuật."""
        return Task(
            description=f"Thực hiện phân tích dữ liệu thị trường toàn diện cho {symbol}. Bao gồm 2 phần: 1. Tìm và tóm tắt 2 tin tức vĩ mô/ngành quan trọng nhất. 2. Sử dụng 'Công cụ tra cứu dữ liệu Phân tích Kỹ thuật' để xác định xu hướng giá và các chỉ báo chính.",
            expected_output=f"Một báo cáo markdown gồm 2 phần rõ rệt: 'Phân tích Tin tức Thị trường' và 'Phân tích Kỹ thuật' cho {symbol}.",
            agent=agent,
            async_execution=False
        )

    def financial_analysis_with_api(self, agent, symbol):
        """Task gọi 'siêu tool'."""
        return Task(
            description=f"Sử dụng 'Công cụ Phân tích Tài chính và Cạnh tranh Toàn diện' với mã cổ phiếu '{symbol}' để tạo ra một báo cáo phân tích tài chính nội tại và so sánh cạnh tranh. Đây là bước cực kỳ quan trọng để hiểu về định giá và hiệu quả hoạt động của công ty so với ngành.",
            expected_output=f"Kết quả đầu ra chính xác từ tool, là một báo cáo Markdown chứa phân tích nội tại và bảng so sánh đối thủ của {symbol}.",
            agent=agent,
            async_execution=False
        )

    def analyze_financial_report_pdf(self, agent, file_path, symbol):
        """Task phân tích file PDF."""
        return Task(
            description=f"Phân tích chuyên sâu báo cáo tài chính của {symbol} từ file PDF tại '{file_path}'. Sử dụng tool OCR để đọc và tóm tắt các điểm chính: tăng trưởng doanh thu/lợi nhuận, biên lợi nhuận, sức khỏe tài chính và dòng tiền.",
            expected_output="Một báo cáo markdown chuyên nghiệp tóm tắt các điểm nổi bật từ báo cáo tài chính PDF.",
            agent=agent,
            async_execution=False
        )

    def comprehensive_analysis_decision(self, agent, symbol, context):
        """Task tổng hợp cuối cùng cho quy trình toàn diện."""
        return Task(
            description=f"Tổng hợp thông tin từ tất cả các báo cáo trước đó (Dữ liệu thị trường, Phân tích tài chính từ PDF, Phân tích tài chính từ API) để đưa ra một quyết định đầu tư cuối cùng cho {symbol}. Phải chấm điểm từng yếu tố (Thị trường, Tài chính) và đưa ra luận điểm sắc bén, thể hiện sự liên kết giữa các nguồn thông tin.",
            expected_output="Một báo cáo đầu tư toàn diện, có luận điểm, bảng điểm, và khuyến nghị hành động (MUA/BÁN/GIỮ).",
            agent=agent,
            context=context
        )