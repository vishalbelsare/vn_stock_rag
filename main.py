# main.py

# Tải biến môi trường ngay từ đầu
from dotenv import load_dotenv
load_dotenv()

import os
import requests
import json
from crewai import Crew, Process
from agents import StockAnalysisAgents
from tasks import StockAnalysisTasks
from datetime import datetime

def get_user_intent_with_mistral(user_query: str) -> dict:
    """
    Sử dụng Mistral AI để phân tích yêu cầu của người dùng.
    """
    try:
        print("Đang dùng Mistral AI để phân tích yêu cầu...")
        API_KEY = os.environ.get("MISTRAL_API_KEY")
        if not API_KEY:
            raise ValueError("Lỗi: MISTRAL_API_KEY chưa được thiết lập.")

        url = "https://api.mistral.ai/v1/chat/completions"
        
        prompt = f"""
        Phân tích yêu cầu của người dùng và trả về một đối tượng JSON.
        Yêu cầu: "{user_query}"

        Các nhiệm vụ có thể có:
        - "analyze_stock": Nếu người dùng chỉ muốn phân tích một mã cổ phiếu.
        - "analyze_pdf": Nếu người dùng chỉ muốn phân tích một file PDF.
        - "comprehensive_analysis": Nếu người dùng muốn phân tích một mã cổ phiếu VÀ có cung cấp một file PDF.
        - "unknown": Nếu không xác định được.

        Đối tượng JSON phải có 3 trường: "task", "ticker", "file_path".
        - "task": điền một trong các giá trị trên.
        - "ticker": trích xuất mã cổ phiếu (chuỗi 3-4 ký tự viết hoa). Nếu không có, điền null.
        - "file_path": trích xuất đường dẫn file PDF. Nếu không có, điền null.

        Chỉ trả về đối tượng JSON, không giải thích gì thêm.
        """
        payload = { "model": "mistral-large-latest", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"} }
        headers = { "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Accept": "application/json" }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        intent_data = json.loads(response.json()["choices"][0]["message"]["content"])
        print(f"Mistral đã phân tích yêu cầu: {intent_data}")
        return intent_data
    except Exception as e:
        print(f"Lỗi khi phân tích yêu cầu: {e}")
        return {"task": "unknown", "ticker": None, "file_path": None}

class FinancialCrew:
    """
    Class quản lý việc khởi tạo và chạy các quy trình phân tích của Crew đã được tối ưu.
    """
    def __init__(self, symbol=None, file_path=None):
        self.symbol = symbol
        self.file_path = file_path
        self.agents = StockAnalysisAgents()
        self.tasks = StockAnalysisTasks()

    def run_stock_analysis(self):
        """Chạy quy trình phân tích cổ phiếu cơ bản (không có file PDF)."""
        market_analyst = self.agents.market_data_analyst()
        financial_analyst_agent = self.agents.financial_analyst()
        investment_strategist = self.agents.investment_strategist()

        market_task = self.tasks.market_analysis(market_analyst, self.symbol)
        financial_task = self.tasks.financial_analysis_with_api(financial_analyst_agent, self.symbol)
        
        # Task tổng hợp cho quy trình này sẽ không có context từ PDF
        # Chúng ta có thể tạo một task `investment_decision` riêng hoặc dùng chung `comprehensive_analysis_decision`
        # và AI sẽ tự biết là thiếu context PDF.
        decision_task = self.tasks.comprehensive_analysis_decision(
            investment_strategist, self.symbol,
            [market_task, financial_task] 
        )
        
        crew = Crew(
            agents=[market_analyst, financial_analyst_agent, investment_strategist],
            tasks=[market_task, financial_task, decision_task],
            process=Process.sequential, verbose=True, cache=True
        )
        return crew.kickoff()

    def run_pdf_analysis(self):
        """Chạy quy trình chỉ phân tích file PDF."""
        financial_analyst_agent = self.agents.financial_analyst()
        pdf_task = self.tasks.analyze_financial_report_pdf(
            agent=financial_analyst_agent, file_path=self.file_path, symbol=self.symbol
        )
        crew = Crew(
            agents=[financial_analyst_agent], 
            tasks=[pdf_task], 
            verbose=True, cache=True
        )
        return crew.kickoff()

    def run_comprehensive_analysis(self):
        """Chạy quy trình phân tích toàn diện, kết hợp mọi nguồn thông tin."""
        market_analyst = self.agents.market_data_analyst()
        financial_analyst_agent = self.agents.financial_analyst()
        investment_strategist = self.agents.investment_strategist()

        market_task = self.tasks.market_analysis(market_analyst, self.symbol)
        pdf_task = self.tasks.analyze_financial_report_pdf(financial_analyst_agent, self.file_path, self.symbol)
        financial_api_task = self.tasks.financial_analysis_with_api(financial_analyst_agent, self.symbol)
        
        comprehensive_task = self.tasks.comprehensive_analysis_decision(
            investment_strategist, self.symbol,
            [market_task, pdf_task, financial_api_task]
        )
        
        crew = Crew(
            agents=[market_analyst, financial_analyst_agent, investment_strategist],
            tasks=[market_task, pdf_task, financial_api_task, comprehensive_task],
            process=Process.sequential, verbose=True, cache=True
        )
        return crew.kickoff()

def run_analysis_workflow(user_input):
    """
    Hàm điều phối chính, được gọi bởi cả giao diện Streamlit và dòng lệnh.
    """
    intent = get_user_intent_with_mistral(user_input)
    result = None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = ""

    task_type = intent.get('task')
    ticker = intent.get('ticker')
    file_path = intent.get('file_path')

    if task_type == 'comprehensive_analysis' and ticker and file_path:
        print(f"Bắt đầu quy trình phân tích TOÀN DIỆN cho {ticker}...")
        crew_runner = FinancialCrew(symbol=ticker, file_path=file_path)
        result = crew_runner.run_comprehensive_analysis()
        report_filename = f"reports/{ticker.lower()}_comprehensive_analysis_{timestamp}.md"

    elif task_type == 'analyze_stock' and ticker:
        print(f"Bắt đầu quy trình phân tích cổ phiếu: {ticker}...")
        crew_runner = FinancialCrew(symbol=ticker)
        result = crew_runner.run_stock_analysis()
        report_filename = f"reports/{ticker.lower()}_stock_analysis_{timestamp}.md"

    elif task_type == 'analyze_pdf' and file_path:
        print(f"Bắt đầu quy trình phân tích file PDF: {file_path}...")
        crew_runner = FinancialCrew(file_path=file_path, symbol=ticker)
        result = crew_runner.run_pdf_analysis()
        base_name = os.path.basename(file_path).split('.')[0]
        report_filename = f"reports/{base_name}_pdf_analysis_{timestamp}.md"
        
    else:
        return "Không thể xác định yêu cầu của bạn. Vui lòng thử lại với yêu cầu rõ ràng hơn (ví dụ: 'phân tích FPT' hoặc đính kèm file).", None

    if result and hasattr(result, 'raw') and result.raw:
        os.makedirs('reports', exist_ok=True)
        final_report = result.raw
        with open(report_filename, "w", encoding='utf-8') as f:
            f.write(final_report)
        print('--------------------------------------------------')
        print(f"Báo cáo phân tích đã được lưu tại: {report_filename}")
        return final_report, report_filename
    
    error_message = f"Đã xảy ra lỗi trong quá trình phân tích. Kết quả trả về không hợp lệ: {result}"
    print(error_message)
    return error_message, None

# Khối này chỉ được thực thi khi bạn chạy `python main.py` trực tiếp
if __name__ == "__main__":
    print("## Chào mừng bạn đến với Crew Phân tích Cổ phiếu ##")
    user_input_cli = input("Nhập yêu cầu của bạn: ")
    
    final_report_cli, filename_cli = run_analysis_workflow(user_input_cli)
    
    if filename_cli:
        print("\n--- BÁO CÁO CUỐI CÙNG ---")
        print(final_report_cli)
    else:
        print("\n--- LỖI ---")
        print(final_report_cli) # In ra thông báo lỗi