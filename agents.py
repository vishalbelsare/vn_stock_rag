# agents.py

import os
from crewai import Agent, LLM

# Import các công cụ
from tools.search_tools import search_tool, scrape_tool
from tools.financial_tools import ComprehensiveFinancialTool, TechDataTool
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
GEMINI_PRO_MODEL = 'gemini/gemini-2.5-pro'

llm_flash = LLM(
    model=GEMINI_FLASH_MODEL, api_key=os.environ.get("GOOGLE_API_KEY"),
    temperature=0.2, max_tokens=4096, **retry_config, **safety_settings_config
)
llm_pro = LLM(
    model=GEMINI_PRO_MODEL, api_key=os.environ.get("GOOGLE_API_KEY"),
    temperature=0.3, max_tokens=8192, **retry_config, **safety_settings_config
)

# Khởi tạo các công cụ
comprehensive_financial_tool = ComprehensiveFinancialTool()
tech_tool = TechDataTool()
file_read_tool = FileReadTool()
ocr_tool = MistralOCRTool()

class StockAnalysisAgents():
    """Class chứa 3 agent đã được tối ưu."""
    def market_data_analyst(self):
        """Agent hợp nhất: Phân tích tin tức và kỹ thuật."""
        return Agent(
            role='Nhà phân tích Dữ liệu Thị trường.',
            goal='Cung cấp một cái nhìn tổng quan về bối cảnh thị trường xung quanh một cổ phiếu, bao gồm cả tin tức vĩ mô và xu hướng giá kỹ thuật.',
            backstory='Bạn là một nhà phân tích nhanh nhạy, có khả năng tổng hợp cả thông tin định tính (tin tức) và định lượng (giá, khối lượng) để đưa ra bức tranh toàn cảnh về thị trường.',
            verbose=True,
            tools=[search_tool, scrape_tool, tech_tool],
            llm=llm_flash,
            allow_delegation=False
        )

    def financial_analyst(self):
        """Agent phân tích tài chính sâu, sử dụng siêu tool và OCR."""
        return Agent(
            role='Chuyên gia Phân tích Tài chính Doanh nghiệp.',
            goal='Thực hiện phân tích sâu về tài chính công ty, dựa trên cả dữ liệu API (qua "siêu tool") và tài liệu PDF.',
            backstory='Bạn là chuyên gia về tài chính doanh nghiệp, có khả năng "đọc vị" sức khỏe tài chính của một công ty từ nhiều nguồn dữ liệu khác nhau.',
            verbose=True,
            tools=[comprehensive_financial_tool, ocr_tool, file_read_tool],
            llm=llm_flash,
            allow_delegation=False
        )

    def investment_strategist(self):
        """Agent tổng hợp cuối cùng."""
        return Agent(
            role='Chuyên gia Chiến lược Đầu tư.',
            goal='Tổng hợp tất cả các phân tích (thị trường, tài chính) để đưa ra khuyến nghị đầu tư cuối cùng.',
            backstory='Bạn là giám đốc đầu tư, người đưa ra quyết định cuối cùng dựa trên tất cả các báo cáo.',
            verbose=True,
            llm=llm_pro,
            allow_delegation=True
        )