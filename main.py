# main.py

# Tải biến môi trường ngay từ đầu để tất cả các module khác đều có thể sử dụng
from dotenv import load_dotenv
load_dotenv()

import os
import requests
import json
from crewai import Crew, Process
from agents import StockAnalysisAgents  # agents.py bây giờ có financial_analyst
from tasks import StockAnalysisTasks      # tasks.py bây giờ có financial_analysis
from datetime import datetime

def get_user_intent_with_mistral(user_query: str) -> dict:
    """
    Sử dụng Mistral AI qua API request để phân tích và hiểu ý định của người dùng.
    Hàm này trả về một dictionary chứa thông tin về tác vụ, mã cổ phiếu và đường dẫn file.
    """
    try:
        print("Đang dùng Mistral AI để phân tích yêu cầu...")
        API_KEY = os.environ.get("MISTRAL_API_KEY")
        if not API_KEY:
            raise ValueError("Lỗi: MISTRAL_API_KEY chưa được thiết lập trong file .env.")

        url = "https://api.mistral.ai/v1/chat/completions"
        
        prompt = f"""
        Phân tích yêu cầu của người dùng và trả về một đối tượng JSON.
        Yêu cầu: "{user_query}"

        Các nhiệm vụ có thể có:
        - "analyze_stock": Nếu người dùng chỉ muốn phân tích một mã cổ phiếu.
        - "analyze_pdf": Nếu người dùng chỉ muốn phân tích một file PDF.
        - "comprehensive_analysis": Nếu người dùng muốn phân tích một mã cổ phiếu VÀ có cung cấp một file PDF báo cáo tài chính đi kèm.
        - "unknown": Nếu không xác định được.

        Đối tượng JSON phải có 3 trường: "task", "ticker", "file_path".
        - "task": điền một trong các giá trị trên.
        - "ticker": trích xuất mã cổ phiếu (chuỗi 3-4 ký tự viết hoa). Nếu không có, điền null.
        - "file_path": trích xuất đường dẫn file PDF. Nếu không có, điền null.

        Chỉ trả về đối tượng JSON, không giải thích gì thêm.

        Ví dụ 1 (Chỉ cổ phiếu): "phân tích fpt" -> {{"task": "analyze_stock", "ticker": "FPT", "file_path": null}}
        Ví dụ 2 (Chỉ PDF): "tóm tắt file C:/bctc.pdf" -> {{"task": "analyze_pdf", "ticker": null, "file_path": "C:/bctc.pdf"}}
        Ví dụ 3 (Toàn diện): "phân tích cổ phiếu FPT dựa vào báo cáo này D:\\data\\FPT_Q2.pdf" -> {{"task": "comprehensive_analysis", "ticker": "FPT", "file_path": "D:\\\\data\\\\FPT_Q2.pdf"}}
        """
        payload = { "model": "mistral-large-latest", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"} }
        headers = { "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "Accept": "application/json" }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        intent_data = json.loads(response.json()["choices"][0]["message"]["content"])
        
        print(f"Mistral đã phân tích yêu cầu: {intent_data}")
        return intent_data

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi API Mistral: {e}")
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        print(f"Lỗi khi xử lý phản hồi JSON từ Mistral: {e}")
    except Exception as e:
        print(f"Lỗi không xác định khi phân tích yêu cầu: {e}")
        
    # Fallback nếu có lỗi xảy ra
    return {"task": "unknown", "ticker": None, "file_path": None}

class FinancialCrew:
    """
    Class quản lý việc khởi tạo và chạy các quy trình phân tích của Crew.
    """
    def __init__(self, symbol=None, file_path=None):
        self.symbol = symbol
        self.file_path = file_path
        self.agents = StockAnalysisAgents()
        self.tasks = StockAnalysisTasks()

    def run_stock_analysis(self):
        """Chạy quy trình phân tích cổ phiếu cơ bản (không có file PDF)."""
        # Khởi tạo các agent cần thiết từ class agents
        news_researcher = self.agents.stock_news_researcher()
        financial_analyst_agent = self.agents.financial_analyst() # Gọi agent đã hợp nhất
        technical_analyst = self.agents.technical_analyst()
        investment_strategist = self.agents.investment_strategist()

        # Tạo các task tương ứng
        news_task = self.tasks.news_collecting(news_researcher, self.symbol)
        financial_task = self.tasks.financial_analysis(financial_analyst_agent, self.symbol) # Gọi task đã hợp nhất
        technical_task = self.tasks.technical_analysis(technical_analyst, self.symbol)
        
        investment_task = self.tasks.investment_decision(
            investment_strategist, self.symbol,
            [news_task, financial_task, technical_task] # Context bây giờ chỉ cần 3 task
        )
        
        crew = Crew(
            agents=[news_researcher, financial_analyst_agent, technical_analyst, investment_strategist],
            tasks=[news_task, financial_task, technical_task, investment_task],
            process=Process.sequential, verbose=True, cache=True
        )
        return crew.kickoff()

    def run_pdf_analysis(self):
        """Chạy quy trình chỉ phân tích file PDF."""
        # Agent financial_analyst giờ đã có tool OCR
        pdf_analyzer_agent = self.agents.financial_analyst() 
        pdf_task = self.tasks.analyze_financial_report(
            agent=pdf_analyzer_agent,
            file_path=self.file_path,
            company_ticker=self.symbol
        )
        crew = Crew(
            agents=[pdf_analyzer_agent], 
            tasks=[pdf_task], 
            verbose=True, cache=True
        )
        return crew.kickoff()

    def run_comprehensive_analysis(self):
        """Chạy quy trình phân tích toàn diện, kết hợp mọi nguồn thông tin."""
        # Khởi tạo các agent cần thiết
        news_researcher = self.agents.stock_news_researcher()
        technical_analyst = self.agents.technical_analyst()
        financial_analyst_agent = self.agents.financial_analyst() # Agent đa năng
        investment_strategist = self.agents.investment_strategist()

        # Tạo các task
        news_task = self.tasks.news_collecting(news_researcher, self.symbol)
        tech_task = self.tasks.technical_analysis(technical_analyst, self.symbol)
        pdf_analysis_task = self.tasks.analyze_financial_report(financial_analyst_agent, self.file_path, self.symbol)
        financial_comp_task = self.tasks.financial_analysis(financial_analyst_agent, self.symbol) # Task hợp nhất

        comprehensive_task = self.tasks.comprehensive_stock_analysis(
            agent=investment_strategist,
            symbol=self.symbol,
            context=[news_task, tech_task, pdf_analysis_task, financial_comp_task]
        )
        
        crew = Crew(
            agents=[news_researcher, technical_analyst, financial_analyst_agent, investment_strategist],
            tasks=[news_task, tech_task, pdf_analysis_task, financial_comp_task, comprehensive_task],
            process=Process.sequential, verbose=True, cache=True
        )
        return crew.kickoff()

def run_analysis_workflow(user_input):
    """
    Hàm điều phối chính, được gọi bởi cả giao diện Streamlit và dòng lệnh.
    Phân tích yêu cầu người dùng và khởi chạy quy trình phù hợp.
    """
    intent = get_user_intent_with_mistral(user_input)
    result = None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = "" # Khởi tạo report_filename

    if intent.get('task') == 'comprehensive_analysis' and intent.get('ticker') and intent.get('file_path'):
        print(f"Bắt đầu quy trình phân tích TOÀN DIỆN cho {intent['ticker']}...")
        crew_runner = FinancialCrew(symbol=intent['ticker'], file_path=intent['file_path'])
        result = crew_runner.run_comprehensive_analysis()
        report_filename = f"reports/{intent['ticker'].lower()}_comprehensive_analysis_{timestamp}.md"

    elif intent.get('task') == 'analyze_stock' and intent.get('ticker'):
        print(f"Bắt đầu quy trình phân tích cổ phiếu: {intent['ticker']}...")
        crew_runner = FinancialCrew(symbol=intent['ticker'])
        result = crew_runner.run_stock_analysis()
        report_filename = f"reports/{intent['ticker'].lower()}_stock_analysis_{timestamp}.md"

    elif intent.get('task') == 'analyze_pdf' and intent.get('file_path'):
        print(f"Bắt đầu quy trình phân tích file PDF: {intent['file_path']}...")
        crew_runner = FinancialCrew(file_path=intent['file_path'], symbol=intent.get('ticker'))
        result = crew_runner.run_pdf_analysis()
        base_name = os.path.basename(intent['file_path']).split('.')[0]
        report_filename = f"reports/{base_name}_pdf_analysis_{timestamp}.md"
        
    else:
        return "Không thể xác định yêu cầu của bạn. Vui lòng thử lại.", None

    # Kiểm tra kết quả an toàn trước khi ghi file
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