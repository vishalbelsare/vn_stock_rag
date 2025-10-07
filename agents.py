# agents.py

import os
from crewai import Agent, LLM

# Import các công cụ
from tools.search_tools import search_tool, scrape_tool
from tools.financial_tools import FundDataTool, TechDataTool
from tools.file_tools import FileReadTool
from tools.ocr_tool import MistralOCRTool

# Cấu hình an toàn và retry cho Gemini
safety_settings_config = {
    "safety_settings": [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
}
retry_config = {"num_retries": 3, "retry_on_failure": True}

# Khởi tạo LLM
GEMINI_FLASH_MODEL = 'gemini/gemini-2.5-flash'
GEMINI_PRO_MODEL = 'gemini/gemini-2.5-flash'

llm_flash = LLM(
    model=GEMINI_FLASH_MODEL, api_key=os.environ.get("GOOGLE_API_KEY"),
    temperature=0.2, max_tokens=4096, **retry_config, **safety_settings_config
)
llm_pro = LLM(
    model=GEMINI_PRO_MODEL, api_key=os.environ.get("GOOGLE_API_KEY"),
    temperature=0.3, max_tokens=8192, **retry_config, **safety_settings_config
)

# Khởi tạo các công cụ
fund_tool = FundDataTool()
tech_tool = TechDataTool()
file_read_tool = FileReadTool()
ocr_tool = MistralOCRTool()

class StockAnalysisAgents():
    """
    Class chứa tất cả các agent cho quy trình phân tích.
    """
    def stock_news_researcher(self):
        return Agent(
            role='Chuyên gia Phân tích Tin tức Vĩ mô và Ngành.',
            goal='Tìm kiếm, sàng lọc và tóm tắt các tin tức vĩ mô và ngành quan trọng ảnh hưởng đến thị trường và cổ phiếu mục tiêu.',
            backstory=(
                'Với kinh nghiệm báo chí kinh tế, bạn có khả năng nhận diện tin tức có tác động mạnh mẽ nhất. '
                'Khi dùng tool, hãy tuân thủ định dạng: Thought, Action, Action Input.'
            ),
            verbose=True, tools=[search_tool, scrape_tool], llm=llm_flash, allow_delegation=False
        )

    def financial_analyst(self):
        """Agent đã được hợp nhất: Phân tích cơ bản, đối thủ, và báo cáo tài chính."""
        return Agent(
            role='Chuyên gia Phân tích Tài chính Doanh nghiệp Toàn diện.',
            goal='Đánh giá sức khỏe tài chính của công ty, so sánh với đối thủ, và phân tích sâu báo cáo tài chính (PDF).',
            backstory=(
                'Bạn là một nhà phân tích tài chính sắc sảo, có khả năng phân tích cả số liệu nội tại và bối cảnh cạnh tranh của ngành. '
                'Khi dùng tool, hãy tuân thủ định dạng: Thought, Action, Action Input.'
            ),
            verbose=True, tools=[search_tool, fund_tool, file_read_tool, ocr_tool], llm=llm_flash, allow_delegation=False
        )

    def technical_analyst(self):
        return Agent(
            role='Nhà phân tích Kỹ thuật.',
            goal='Xác định xu hướng giá, các vùng hỗ trợ/kháng cự và tín hiệu giao dịch dựa trên biểu đồ và chỉ báo.',
            backstory=(
                'Bạn là một trader kỷ luật, quyết định dựa trên dữ liệu giá và khối lượng, không bị ảnh hưởng bởi cảm tính. '
                'Khi dùng tool, hãy tuân thủ định dạng: Thought, Action, Action Input.'
            ),
            verbose=True, tools=[tech_tool], llm=llm_flash, allow_delegation=False
        )

    def investment_strategist(self):
        return Agent(
            role='Chuyên gia Chiến lược Đầu tư.',
            goal='Tổng hợp tất cả các phân tích để đưa ra khuyến nghị đầu tư cuối cùng (MUA/BÁN/GIỮ) kèm theo luận điểm rõ ràng.',
            backstory='Bạn là giám đốc đầu tư, có trách nhiệm đưa ra quyết định cuối cùng dựa trên tất cả thông tin có sẵn.',
            verbose=True, llm=llm_pro, allow_delegation=True
        )