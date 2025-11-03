# agents.py

import os
from crewai import Agent, LLM
from key_manager import key_manager
from tools.search_tools import search_tool, scrape_tool
from tools.financial_tools import ComprehensiveFinancialTool, TechDataTool
from tools.file_tools import FileReadTool
from tools.ocr_tool import MistralOCRTool
from tools.charting_tool import ChartingTool

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
    """
    Hàm trợ giúp để tạo một instance LLM với một API key mới được
    lấy một cách xoay vòng từ KeyManager.
    """
    return LLM(
        model=model_name,
        api_key=key_manager.get_next_key(),
        temperature=0.2 if 'flash' in model_name else 0.3,
        max_tokens=4096 if 'flash' in model_name else 8192,
        **retry_config,
        **safety_settings_config
    )

comprehensive_financial_tool = ComprehensiveFinancialTool()
tech_tool = TechDataTool()
file_read_tool = FileReadTool()
ocr_tool = MistralOCRTool()
charting_tool = ChartingTool()


class StockAnalysisAgents():
    """
    Class chứa 5 agent chuyên biệt.
    Mỗi agent sẽ được tạo với một instance LLM riêng, sử dụng một API key khác nhau.
    """

    def __init__(self):
        """
        Khởi tạo các instance LLM ngay khi class được tạo ra.
        Điều này đảm bảo mỗi agent sẽ có một LLM với key riêng.
        """
        # Tạo 4 instance LLM Flash cho các agent phụ
        self.llm_flash_1 = create_llm(GEMINI_FLASH_MODEL)
        self.llm_flash_2 = create_llm(GEMINI_FLASH_MODEL)
        self.llm_flash_3 = create_llm(GEMINI_FLASH_MODEL)
        self.llm_flash_4 = create_llm(GEMINI_FLASH_MODEL)
        # Tạo 1 instance LLM Pro cho agent tổng hợp
        self.llm_pro_editor = create_llm(GEMINI_PRO_MODEL)

    def market_news_analyst(self):
        """Agent chuyên về tin tức vĩ mô và ngành."""
        return Agent(
            role='Chuyên gia Phân tích Tin tức Thị trường.',
            goal='Tìm kiếm, chắt lọc và tóm tắt những tin tức vĩ mô và chính sách quan trọng nhất đang ảnh hưởng đến thị trường chứng khoán Việt Nam.',
            backstory=(
                'Bạn là một nhà báo kinh tế nhạy bén, chuyên theo dõi các động thái của chính phủ và ngân hàng nhà nước. '
                'Bạn có khả năng diễn giải các chính sách và dự báo tác động của chúng lên thị trường chung.'
            ),
            verbose=True,
            tools=[search_tool, scrape_tool],
            llm=self.llm_flash_1, 
            allow_delegation=False
        )

    def technical_analyst(self):
        """Agent chuyên về phân tích kỹ thuật cho chỉ số chung."""
        return Agent(
            role='Nhà phân tích Kỹ thuật (Chartist).',
            goal='Phân tích biểu đồ giá và khối lượng của chỉ số VN-Index, xác định các xu hướng, ngưỡng hỗ trợ/kháng cự và đưa ra nhận định kỹ thuật khách quan.',
            backstory=(
                'Bạn là một chuyên gia phân tích kỹ thuật với nhiều năm kinh nghiệm, tuân thủ nghiêm ngặt các nguyên tắc của mình. '
                'Phân tích của bạn chỉ dựa trên dữ liệu biểu đồ và các chỉ báo, không bị chi phối bởi cảm tính hay tin tức.'
            ),
            verbose=True,
            tools=[tech_tool, charting_tool],
            llm=self.llm_flash_2, 
            allow_delegation=False
        )

    def financial_competitor_analyst(self):
        """Agent chuyên về phân tích tài chính và đối thủ của một cổ phiếu cụ thể."""
        return Agent(
            role='Chuyên gia Phân tích Tài chính Doanh nghiệp và Cạnh tranh.',
            goal='Sử dụng các công cụ để tạo ra một báo cáo phân tích tài chính nội tại và so sánh một cổ phiếu cụ thể với các đối thủ cạnh tranh chính trong ngành.',
            backstory=(
                'Bạn là một nhà phân tích tài chính chuyên sâu, có khả năng đánh giá nhanh sức khỏe và vị thế cạnh tranh của một doanh nghiệp thông qua các chỉ số định lượng. '
                'Bạn luôn đặt câu hỏi "Công ty này tốt như thế nào so với những công ty khác?"'
            ),
            verbose=True,
            tools=[comprehensive_financial_tool],
            llm=self.llm_flash_3, 
            allow_delegation=False
        )

    def financial_report_analyst(self):
        """Agent chuyên phân tích file PDF báo cáo tài chính."""
        return Agent(
            role='Chuyên gia Phân tích Báo cáo Tài chính (PDF).',
            goal='Đọc và trích xuất những thông tin cốt lõi, những con số "biết nói" từ một file PDF báo cáo tài chính được cung cấp bởi người dùng.',
            backstory=(
                'Bạn có khả năng đặc biệt trong việc đọc hiểu các tài liệu tài chính dày đặc và phức tạp. '
                'Nhiệm vụ của bạn là chắt lọc những thông tin quan trọng nhất về kết quả kinh doanh, sức khỏe tài chính và dòng tiền, rồi tóm tắt chúng một cách rõ ràng.'
            ),
            verbose=True,
            tools=[ocr_tool, file_read_tool],
            llm=self.llm_flash_4, 
            allow_delegation=False
        )
    
    def report_editor(self):
        """Agent "Tổng biên tập", tổng hợp và định dạng báo cáo cuối cùng."""
        return Agent(
            role='Tổng biên tập Bản tin Chứng khoán.',
            goal='Tổng hợp, biên tập và định dạng tất cả các báo cáo phân tích từ các chuyên gia khác để tạo ra một Bản tin Chứng khoán hoàn chỉnh, chuyên nghiệp và liền mạch, có văn phong giống như các công ty chứng khoán hàng đầu.',
            backstory=(
                'Bạn là một tổng biên tập giàu kinh nghiệm, có con mắt tinh tường về bố cục, văn phong và khả năng kết nối các phần thông tin rời rạc thành một câu chuyện tổng thể, hấp dẫn cho nhà đầu tư. '
                'Bạn sẽ nhận các báo cáo riêng lẻ và biến chúng thành một sản phẩm cuối cùng duy nhất, chất lượng cao.'
            ),
            verbose=True,
            llm=self.llm_pro_editor, 
            allow_delegation=False 
        )