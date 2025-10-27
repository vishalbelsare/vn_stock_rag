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
import sys

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
    def __init__(self, symbol=None, file_path=None):
        self.symbol = symbol
        self.file_path = file_path
        self.agents = StockAnalysisAgents()
        self.tasks = StockAnalysisTasks()

    def run_stock_analysis(self):
        """Chạy quy trình phân tích cổ phiếu cơ bản (4 agents)."""
        news_analyst = self.agents.market_news_analyst()
        tech_analyst = self.agents.technical_analyst()
        fin_comp_analyst = self.agents.financial_competitor_analyst()
        editor = self.agents.report_editor() # Dùng editor để tổng hợp

        market_task = self.tasks.market_news_analysis(news_analyst)
        tech_task = self.tasks.technical_analysis(tech_analyst, self.symbol)
        fin_comp_task = self.tasks.financial_competitor_analysis(fin_comp_analyst, self.symbol)
        
        # Yêu cầu editor tổng hợp 3 báo cáo này
        compose_task = self.tasks.compose_newsletter(
            editor,
            context=[market_task, tech_task, fin_comp_task],
            symbol=self.symbol
        )
        
        crew = Crew(
            agents=[news_analyst, tech_analyst, fin_comp_analyst, editor],
            tasks=[market_task, tech_task, fin_comp_task, compose_task],
            process=Process.sequential, verbose=True, cache=True
        )
        return crew.kickoff()

    def run_pdf_analysis(self):
        """Chạy quy trình chỉ phân tích file PDF (1 agent)."""
        pdf_analyst = self.agents.financial_report_analyst()
        pdf_task = self.tasks.analyze_pdf_report(
            agent=pdf_analyst, file_path=self.file_path
        )
        crew = Crew(
            agents=[pdf_analyst], 
            tasks=[pdf_task], 
            verbose=True, cache=True
        )
        return crew.kickoff()

    def run_newsletter_creation(self):
        """Chạy quy trình 5 agent để tạo bản tin chứng khoán hoàn chỉnh."""
        market_analyst = self.agents.market_news_analyst()
        tech_analyst = self.agents.technical_analyst()
        fin_comp_analyst = self.agents.financial_competitor_analyst()
        pdf_analyst = self.agents.financial_report_analyst()
        editor = self.agents.report_editor()

        market_task = self.tasks.market_news_analysis(market_analyst)
        tech_task = self.tasks.technical_analysis(tech_analyst, self.symbol)
        fin_comp_task = self.tasks.financial_competitor_analysis(fin_comp_analyst, self.symbol)
        pdf_task = self.tasks.analyze_pdf_report(pdf_analyst, self.file_path)

        compose_task = self.tasks.compose_newsletter(
            editor,
            context=[market_task, tech_task, fin_comp_task, pdf_task],
            symbol=self.symbol
        )
        
        crew = Crew(
            agents=[market_analyst, tech_analyst, fin_comp_analyst, pdf_analyst, editor],
            tasks=[market_task, tech_task, fin_comp_task, pdf_task, compose_task],
            process=Process.sequential,
            verbose=True,
            cache=True
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

    print("\n" + "#"*50)
    print("DEBUG TRẠM 2: BÊN TRONG MAIN.PY (full_analysis_process)")
    print(f"Loại dữ liệu của user_query: {type(user_input)}")
    print(f"Nội dung user_query nhận được từ api.py:\n---\n{user_input}\n---\n")
    print("#"*50 + "\n")


    if (task_type == 'create_newsletter' or task_type == 'comprehensive_analysis') and ticker and file_path:
        print(f"Bắt đầu quy trình tạo Bản tin Toàn diện cho {ticker}...")
        crew_runner = FinancialCrew(symbol=ticker, file_path=file_path)
        result = crew_runner.run_newsletter_creation()
        report_filename = f"reports/BanTin_{ticker}_{timestamp}.md"

    elif task_type == 'analyze_stock' and ticker:
        print(f"Bắt đầu quy trình phân tích cổ phiếu: {ticker}...")
        crew_runner = FinancialCrew(symbol=ticker)
        result = crew_runner.run_stock_analysis()
        report_filename = f"reports/PhanTich_{ticker}_{timestamp}.md"

    elif task_type == 'analyze_pdf' and file_path:
        print(f"Bắt đầu quy trình phân tích file PDF: {file_path}...")
        crew_runner = FinancialCrew(file_path=file_path, symbol=ticker)
        result = crew_runner.run_pdf_analysis()
        base_name = os.path.basename(file_path).split('.')[0]
        report_filename = f"reports/TomTat_{base_name}_{timestamp}.md"
        
    else:
        return "Không thể xác định yêu cầu của bạn. Vui lòng cung cấp yêu cầu rõ ràng hơn (ví dụ: 'phân tích FPT' hoặc 'tạo bản tin cho HPG' và đính kèm file).", None

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
    print("## Chào mừng bạn đến với Trợ lý Phân tích AI ##")
    user_input_cli = input("Nhập yêu cầu của bạn: ")
    
    final_report_cli, filename_cli = run_analysis_workflow(user_input_cli)
    
    if filename_cli:
        print("\n--- BÁO CÁO HOÀN CHỈNH ---")
        print(final_report_cli)
    else:
        print("\n--- LỖI ---")
        print(final_report_cli)

# if __name__ == "__main__":
#     # Kiểm tra xem có nhận được đối số từ dòng lệnh không
#     if len(sys.argv) < 2:
#         print("Lỗi: Vui lòng cung cấp chuỗi yêu cầu của người dùng làm đối số.")
#         sys.exit(1)
        
#     # Lấy chuỗi yêu cầu từ đối số dòng lệnh
#     user_query = sys.argv[1]
    
#     # --- LOGIC ĐIỀU PHỐI ĐƯỢC CHUYỂN VỀ ĐÂY ---
#     try:
#         print("Bắt đầu phân tích yêu cầu người dùng...")
#         intent = get_user_intent_with_mistral(user_query)
        
#         ticker = intent.get('ticker')
#         file_path = intent.get('file_path')

#         result = None
#         crew_runner = FinancialCrew(symbol=ticker, file_path=file_path)

#         if ticker and file_path:
#             print(f"\nBắt đầu quy trình tạo Bản tin Toàn diện cho {ticker}...\n")
#             result = crew_runner.run_newsletter_creation()
#         elif ticker and not file_path:
#             print(f"\nBắt đầu quy trình phân tích cổ phiếu {ticker}...\n")
#             result = crew_runner.run_stock_analysis()
#         elif file_path and not ticker:
#             print(f"\nBắt đầu quy trình phân tích file PDF...\n")
#             result = crew_runner.run_pdf_analysis()
#         else:
#             raise ValueError("Không thể xác định yêu cầu từ chuỗi đầu vào.")

#         final_report = result.raw if result and hasattr(result, 'raw') else "Không có báo cáo được tạo ra."
        
#         # In một dấu hiệu đặc biệt để api.py biết rằng đây là kết quả cuối cùng
#         print("\n---FINAL_REPORT_START---")
#         print(final_report)
#         print("---FINAL_REPORT_END---")

#     except Exception as e:
#         print(f"\n---ERROR_START---")
#         print(f"Đã xảy ra lỗi trong quá trình xử lý: {e}")
#         import traceback
#         traceback.print_exc()
#         print(f"---ERROR_END---")
