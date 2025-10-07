# tasks.py

from crewai import Task
from datetime import datetime

class StockAnalysisTasks():
    """
    Class chứa tất cả các task cho các quy trình phân tích.
    """
    def news_collecting(self, agent, symbol):
        return Task(
            description=f"Tìm và tóm tắt 3 tin tức vĩ mô/ngành quan trọng nhất ảnh hưởng đến cổ phiếu {symbol} trong 3 tháng qua. Ngày hiện tại: {datetime.now().strftime('%Y-%m-%d')}.",
            expected_output="Một báo cáo markdown tóm tắt 3 bài báo, mỗi bài gồm: Tiêu đề, Nguồn, Tóm tắt và Phân tích tác động.",
            agent=agent,
            async_execution=False
        )

    def financial_analysis(self, agent, symbol):
        """Task hợp nhất: Phân tích cơ bản và phân tích đối thủ."""
        return Task(
            description=f"""
                Thực hiện phân tích tài chính toàn diện cho mã cổ phiếu {symbol}, bao gồm cả phân tích nội tại và so sánh cạnh tranh.
                1. Phân tích nội tại: Dùng tool để lấy chỉ số tài chính của {symbol} và so sánh với trung bình ngành.
                2. Phân tích cạnh tranh: Dùng tool tìm kiếm để xác định 2 đối thủ chính, sau đó dùng tool tài chính để lấy chỉ số của họ và tạo bảng so sánh.
            """,
            expected_output=f"Một báo cáo markdown chi tiết về phân tích tài chính của {symbol}, bao gồm phân tích nội tại và một bảng so sánh với các đối thủ cạnh tranh.",
            agent=agent,
            async_execution=False
        )

    def technical_analysis(self, agent, symbol):
        return Task(
            description=f"Thực hiện phân tích kỹ thuật chi tiết cho mã {symbol}. Sử dụng công cụ để lấy các chỉ báo (SMA, RSI, MACD), xác định xu hướng và các vùng giá quan trọng.",
            expected_output="Một báo cáo markdown về phân tích kỹ thuật, bao gồm đánh giá xu hướng, phân tích chỉ báo và xác định các vùng hỗ trợ/kháng cự.",
            agent=agent,
            async_execution=False
        )
    
    def analyze_financial_report(self, agent, file_path, company_ticker=None):
        """Task phân tích file PDF báo cáo tài chính."""
        return Task(
            description=f"Phân tích chuyên sâu báo cáo tài chính từ file PDF tại '{file_path}'. Sử dụng tool OCR để đọc file, sau đó tóm tắt các điểm tài chính quan trọng nhất: tăng trưởng doanh thu/lợi nhuận, biên lợi nhuận, sức khỏe tài chính và dòng tiền.",
            expected_output="Một báo cáo markdown chuyên nghiệp tóm tắt các điểm chính của báo cáo tài chính.",
            agent=agent,
            async_execution=False
        )

    def investment_decision(self, agent, symbol, context):
        """Task tổng hợp cho quy trình phân tích cổ phiếu cơ bản."""
        return Task(
            description=f"Tổng hợp thông tin từ các phân tích vĩ mô, tài chính (nội tại & cạnh tranh), và kỹ thuật để đưa ra chiến lược đầu tư cuối cùng cho mã {symbol}. Chấm điểm từng yếu tố và đưa ra khuyến nghị (MUA/BÁN/GIỮ).",
            expected_output="Một báo cáo đầu tư hoàn chỉnh có luận điểm, bảng điểm, và khuyến nghị hành động rõ ràng.",
            agent=agent,
            context=context
        )

    def comprehensive_stock_analysis(self, agent, symbol, context):
        """Task tổng hợp cho quy trình phân tích toàn diện (có PDF)."""
        return Task(
            description=f"Tổng hợp thông tin từ phân tích vĩ mô, kỹ thuật, phân tích BCTC (PDF), và phân tích tài chính/cạnh tranh để đưa ra quyết định đầu tư cuối cùng cho mã {symbol}. Phải thể hiện sự liên kết giữa các nguồn thông tin.",
            expected_output="Một báo cáo đầu tư TOÀN DIỆN có luận điểm sắc bén, kết hợp thông tin từ tất cả các nguồn, có bảng điểm và khuyến nghị hành động rõ ràng.",
            agent=agent,
            context=context
        )