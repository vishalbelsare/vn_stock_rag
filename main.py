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
import google.generativeai as genai
from key_manager import key_manager


def find_latest_report(ticker: str, reports_folder="financial_reports") -> tuple[str, str] | None:
    """
    Tìm báo cáo quý gần nhất cho một mã cổ phiếu.
    Đếm ngược từ Q4 -> Q1 của năm hiện tại.
    Trả về (đường dẫn file, tên quý) hoặc None nếu không tìm thấy.
    """
    print(f"Đang tìm báo cáo gần nhất cho {ticker} trong thư mục {reports_folder}...")
    current_year = datetime.now().year 
    for q in range(4, 0, -1):
        quarter_name = f"Q{q}"
        # Kiểm tra cả .pdf và .PDF
        for ext in ['pdf', 'PDF']:
            file_path = os.path.join(reports_folder, f"{ticker}-{quarter_name}.{ext}")
            if os.path.exists(file_path):
                print(f"Đã tìm thấy báo cáo gần nhất: {file_path}")
                return file_path, quarter_name
    print(f"Không tìm thấy báo cáo nào cho {ticker} trong năm nay.")
    return None

def get_user_intent_with_gemini(user_query: str) -> dict:
    """
    Sử dụng Google Gemini để phân tích yêu cầu của người dùng.
    """
    try:
        print("Đang dùng Gemini AI để phân tích yêu cầu...") # <--- LOG MỚI
        
        api_key = key_manager.get_next_key()
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel('gemini-2.5-flash')

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
        
        response = model.generate_content(prompt)
        
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        
        intent_data = json.loads(cleaned_text)
        print(f"Gemini đã phân tích yêu cầu: {intent_data}")
        return intent_data
        
    except Exception as e:
        print(f"Lỗi khi phân tích yêu cầu bằng Gemini: {e}")
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
        editor = self.agents.report_editor() 

        market_task = self.tasks.market_news_analysis(news_analyst)
        tech_task = self.tasks.technical_analysis(tech_analyst, self.symbol)
        fin_comp_task = self.tasks.financial_competitor_analysis(fin_comp_analyst, self.symbol)
        
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
    intent = get_user_intent_with_gemini(user_input)    
    result = None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = ""

    task_type = intent.get('task')
    ticker = intent.get('ticker')
    file_path = intent.get('file_path')

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

def generate_report_for_ticker(ticker: str) -> tuple[str | None, str | None]:
    print(f"Bắt đầu tạo báo cáo tự động cho mã: {ticker}")
    
    found_report = find_latest_report(ticker, reports_folder="financial_reports")
    
    if found_report:
        file_path, quarter_name = found_report
        user_query = f"tạo bản tin chứng khoán toàn diện cho {ticker} sử dụng file báo cáo {quarter_name} tại '{file_path}'"
    else:
        user_query = f"phân tích cổ phiếu {ticker}"

    print(f"Query mô phỏng cho hệ thống AI: '{user_query}'")
    
    final_report, report_filename = run_analysis_workflow(user_query)
    
    if final_report and "Đã xảy ra lỗi" not in final_report and "Không thể xác định" not in final_report:
        return final_report, report_filename
    else:
        print(f"Lỗi hoặc không có kết quả khi tạo báo cáo cho {ticker}. Chi tiết: {final_report}")
        return None, None


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
