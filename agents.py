# agents.py

import os
from crewai import Agent, LLM
from key_manager import key_manager
from tools.search_tools import search_tool, scrape_tool
from tools.financial_tools import ComprehensiveFinancialTool, TechDataTool
from tools.file_tools import FileReadTool
from tools.ocr_tool import MistralOCRTool
from tools.charting_tool import ChartingTool
from tools.rag_tool import GraphRAGTool

safety_settings_config = {
    "safety_settings": [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
}
retry_config = {"num_retries": 3, "retry_on_failure": True}

GEMINI_FLASH_MODEL = 'gemini/gemini-2.5-flash' 
GEMINI_PRO_MODEL = 'gemini/gemini-2.5-pro'   

def create_llm(model_name: str):
    return LLM(
        model=model_name,
        api_key=key_manager.get_next_key(),
        temperature=0.1, 
        max_tokens=8192,
        **retry_config,
        **safety_settings_config
    )

comprehensive_financial_tool = ComprehensiveFinancialTool()
tech_tool = TechDataTool()
file_read_tool = FileReadTool()
ocr_tool = MistralOCRTool()
charting_tool = ChartingTool()
rag_tool = GraphRAGTool()

class StockAnalysisAgents():
    def __init__(self):
        self.llm_flash_1 = create_llm(GEMINI_FLASH_MODEL)
        self.llm_flash_2 = create_llm(GEMINI_FLASH_MODEL)
        self.llm_flash_3 = create_llm(GEMINI_FLASH_MODEL)
        self.llm_flash_4 = create_llm(GEMINI_FLASH_MODEL)
        self.llm_pro_editor = create_llm(GEMINI_PRO_MODEL) 

    def market_news_analyst(self):
        return Agent(
            role='Chuyên gia Phân tích Vĩ mô & Tin tức.',
            goal='Cung cấp cái nhìn toàn cảnh về thị trường thông qua việc lọc tin tức nhiễu và xác định các sự kiện trọng yếu (Key Events).',
            backstory=(
                'Bạn là một nhà báo kinh tế kỳ cựu với 20 năm kinh nghiệm tại Bloomberg. '
                'Bạn không chỉ đọc tin, bạn "đọc vị" thị trường. Bạn biết tin nào là tin rác để lùa gà, tin nào thực sự ảnh hưởng đến dòng tiền. '
                'Nhiệm vụ của bạn là cảnh báo rủi ro và tìm kiếm cơ hội từ các chính sách vĩ mô.'
            ),
            verbose=True,
            tools=[search_tool, scrape_tool],
            llm=self.llm_flash_1, 
            allow_delegation=False
        )

    def rag_analyst(self):
        return Agent(
            role='Chuyên gia Dữ liệu Báo cáo Tài chính (RAG).',
            goal='Truy xuất chính xác từng con số từ tài liệu PDF nội bộ. Không được phép sai số.',
            backstory=(
                'Bạn là một kiểm toán viên tỉ mỉ. Bạn làm việc với hàng nghìn trang tài liệu PDF. '
                'Trí nhớ của bạn là tuyệt đối dựa trên Vector Database. Nếu tài liệu không nói, bạn sẽ trả lời là không có, tuyệt đối không bịa đặt (hallucinate).'
            ),
            verbose=True,
            tools=[rag_tool], 
            llm=self.llm_flash_4,
            allow_delegation=False
        )

    def technical_analyst(self):
        return Agent(
            role='Nhà chiến lược Phân tích Kỹ thuật (CMT).',
            goal='Đưa ra các điểm Mua/Bán cụ thể dựa trên hành động giá (Price Action) và chỉ báo.',
            backstory=(
                'Bạn tin rằng "Giá phản ánh tất cả". Bạn không quan tâm tin tức, bạn chỉ nhìn vào Chart. '
                'Nhiệm vụ của bạn là xác định xu hướng (Trend) và các vùng quan trọng. '
                'Bạn luôn luôn phải cung cấp BẰNG CHỨNG là hình ảnh biểu đồ cho nhận định của mình.'
            ),
            verbose=True,
            tools=[tech_tool, charting_tool],
            llm=self.llm_flash_2, 
            allow_delegation=False
        )

    def financial_competitor_analyst(self):
        return Agent(
            role='Chuyên gia Phân tích Cạnh tranh Chiến lược.',
            goal='Cung cấp bức tranh toàn cảnh về đối thủ cạnh tranh: Từ chỉ số tài chính đến các động thái kinh doanh mới nhất.',
            backstory=(
                'Bạn không chỉ nhìn vào bảng cân đối kế toán. Bạn hiểu rằng một công ty tốt có thể bị đánh bại bởi một đối thủ đang mở rộng thị phần mạnh mẽ. '
                'Vì vậy, bạn luôn thực hiện quy trình "Kép": '
                '1. So sánh định giá (P/E, ROE). Nếu không có chỉ số nào thì bỏ qua và không nhắc đến chỉ số đó.'
                '2. Điều tra tin tức (Search News): Bạn luôn tìm đọc ít nhất 3 bài báo mới nhất về từng đối thủ để xem họ đang làm gì (Mở nhà máy? Ra sản phẩm mới? Bê bối?).'
            ),
            verbose=True,
            tools=[comprehensive_financial_tool, search_tool], 
            llm=self.llm_flash_3, 
            allow_delegation=False
        )


    def financial_report_analyst(self):
        """Agent OCR cho file PDF tải lên"""
        return Agent(
            role='Chuyên gia Xử lý Dữ liệu Tài liệu.',
            goal='Chuyển đổi các file PDF báo cáo tài chính phức tạp thành văn bản có cấu trúc.',
            backstory=(
                'Nhiệm vụ của bạn là số hóa các báo cáo giấy. Bạn trích xuất bảng cân đối kế toán, báo cáo kết quả kinh doanh một cách chính xác để đồng nghiệp phân tích.'
            ),
            verbose=True,
            tools=[ocr_tool, file_read_tool],
            llm=self.llm_flash_4, 
            allow_delegation=False
        )
    
    def report_editor(self):
        return Agent(
            role='Giám đốc Khối Phân tích (Head of Research).',
            goal='Kiểm duyệt và tổng hợp báo cáo khuyến nghị đầu tư cuối cùng.',
            backstory=(
                'Bạn là người chịu trách nhiệm cuối cùng về chất lượng bản tin gửi khách hàng VIP. '
                'Bạn cực kỳ khắt khe về: '
                '1. SỐ LIỆU: Tiền Việt Nam phải dùng đơn vị "Tỷ đồng" cho số lớn, "đồng" cho giá cổ phiếu. Tuyệt đối không để nguyên số liệu dạng 100.00 gây hiểu lầm. '
                '2. LOGIC: Khuyến nghị Mua/Bán phải khớp với dữ liệu phân tích. Không được nói Tài chính xấu mà lại khuyến nghị Mua dài hạn. '
                '3. TRÌNH BÀY: Báo cáo phải đẹp, chuẩn Markdown, dễ đọc trên điện thoại.'
            ),
            verbose=True,
            llm=self.llm_pro_editor, 
            allow_delegation=False 
        )