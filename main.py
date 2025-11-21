# main.py

from dotenv import load_dotenv
load_dotenv() 

import os
import json
import sys
import google.generativeai as genai
import database_manager as db
from datetime import datetime
from crewai import Crew, Process
from agents import StockAnalysisAgents
from tasks import StockAnalysisTasks
from key_manager import key_manager
from rag_engine import rag_engine
from evaluation_manager import eval_manager

session_storage = {}

def get_or_create_session(session_id):
    if not session_id: return {"history": [], "current_ticker": None, "context_report": ""}
    if session_id not in session_storage:
        session_storage[session_id] = {"history": [], "current_ticker": None, "context_report": ""}
    return session_storage[session_id]


def get_user_intent(user_query: str, has_context: bool = False) -> dict:
    """
    Phân tích ý định. Đã tinh chỉnh Prompt để phân biệt rõ việc "Hỏi thông tin" vs "Yêu cầu phân tích".
    Đặc biệt: Tự động chuẩn hóa tên công ty (BIDV, Hòa Phát...) thành mã chứng khoán (BID, HPG...).
    """
    try:
        print(f"🔍 Gemini đang phân tích ý định: '{user_query}'...")
        
        api_key = key_manager.get_next_key()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        context_info = "Đã có ngữ cảnh hội thoại trước đó." if has_context else "Cuộc hội thoại mới."

        prompt = f"""
        Bạn là bộ định tuyến (Router) thông minh cho hệ thống chứng khoán Việt Nam.
        
        INPUT:
        - Ngữ cảnh: {context_info}
        - Câu hỏi: "{user_query}"

        NHIỆM VỤ 1: PHÂN LOẠI Ý ĐỊNH (3 NHÓM)
        1. "analyze_stock": 
           - Khi người dùng YÊU CẦU: "Phân tích", "Đánh giá", "Soi mã", "Nhận định", "Xem biểu đồ", "Có nên mua".
        2. "chat_with_rag":
           - Khi hỏi CỤ THỂ về SỐ LIỆU TÀI CHÍNH trong báo cáo (Doanh thu, Lợi nhuận, Tài sản, Nợ...).
        3. "chat_direct":
           - Hỏi thông tin sự thật (Fact), kiến thức chung, ai là chủ tịch, trụ sở ở đâu, hoặc chào hỏi.

        NHIỆM VỤ 2: TRÍCH XUẤT VÀ CHUẨN HÓA TICKER (QUAN TRỌNG)
        - Xác định mã cổ phiếu (Ticker) trong câu hỏi.
        - NẾU NGƯỜI DÙNG GỌI TÊN CÔNG TY, HÃY CHUYỂN VỀ MÃ 3 CHỮ CÁI (HOSE/HNX), ví dụ:
           + "BIDV" -> "BID"
           + "Vietcombank" -> "VCB"
           + "Hòa Phát" -> "HPG"
           + "Vinamilk" -> "VNM"
           + "Thế Giới Di Động" -> "MWG"
           + "Vingroup" -> "VIC"
        - Tuyệt đối không trả về sai mã cổ phiếu, nếu người dùng hỏi về BIDV thì mã cổ phiếu phải là BID.

        OUTPUT JSON:
        {{ "type": "analyze_stock" | "chat_with_rag" | "chat_direct", "ticker": "MÃ_CK_3_CHỮ" | null, "file_path": null }}
        """
        
        response = model.generate_content(prompt)
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        intent_data = json.loads(cleaned_text)
        
        if intent_data.get('ticker'):
            intent_data['ticker'] = intent_data['ticker'].upper().strip()

        print(f"✅ Intent: {intent_data['type']} | Ticker: {intent_data['ticker']}")
        return intent_data

    except Exception as e:
        print(f"⚠️ Lỗi phân tích ý định: {e}")
        return {"type": "chat_direct", "ticker": None, "file_path": None}
    
class FinancialCrew:
    def __init__(self, session_id, symbol, file_path=None, status_callback=None):
        self.session_id = session_id
        self.symbol = symbol
        self.file_path = file_path
        self.status_callback = status_callback 
        self.agents = StockAnalysisAgents()
        self.tasks = StockAnalysisTasks()
        messages = db.get_messages(session_id)
        self.history = [{'role': m['role'], 'content': m['content']} for m in messages]

    def _emit(self, msg):
        if self.status_callback: self.status_callback(msg)

    def _step_callback(self, step):
        thought = "Đang xử lý..."
        if hasattr(step, 'tool') and step.tool:
            t = step.tool
            if "Search" in t: thought = "🌍 Đang tìm tin tức..."
            elif "Chart" in t: thought = "📈 Đang vẽ biểu đồ..."
            elif "Financial" in t: thought = "💰 Đang lấy số liệu..."
            else: thought = f"🔧 Tool: {t}"
        self._emit(thought)

    def run(self):
        self.symbol = self.symbol.upper().strip()

        if self.file_path:
            self._emit(f"Đang đọc tài liệu {self.symbol}...")
            try: rag_engine.ingest_pdf(self.file_path, self.symbol)
            except Exception as e: print(f"Ingest Err: {e}")

        self._emit(f"🚀 Bắt đầu phân tích {self.symbol}...")

        base_storage_dir = os.path.abspath("./storage_rag")
        persist_path = os.path.join(base_storage_dir, self.symbol)
        
        has_rag_data = os.path.exists(persist_path) or self.file_path
        
        rag_raw_text = ""
        if has_rag_data:
            self._emit("📑 Đang trích xuất dữ liệu BCTC gốc...")
            query = f"Trích xuất số liệu {self.symbol}: Doanh thu, Lợi nhuận, Tổng tài sản, Nợ, Dòng tiền."
            rag_raw_text = rag_engine.query_data(self.symbol, query, is_deep_analysis=True)
        else:
            self._emit("⚠️ Dùng dữ liệu đại chúng (Không có BCTC nội bộ).")

        market_agent = self.agents.market_news_analyst()
        tech_agent = self.agents.technical_analyst()
        fin_agent = self.agents.financial_competitor_analyst() 
        editor_agent = self.agents.report_editor()

        t_market = self.tasks.market_news_analysis(market_agent)
        t_tech = self.tasks.technical_analysis(tech_agent, self.symbol)
        t_fin = self.tasks.financial_competitor_analysis(fin_agent, self.symbol)
        
        gathering_tasks = [t_market, t_tech, t_fin]
        agents_list = [market_agent, tech_agent, fin_agent, editor_agent]

        t_compose = self.tasks.compose_newsletter(
            editor_agent, 
            context=gathering_tasks, 
            symbol=self.symbol, 
            chat_history=self.history,
            has_rag_data=has_rag_data
        )
        
        if rag_raw_text:
            t_compose.description += f"\n\n=== DỮ LIỆU TỪ BÁO CÁO TÀI CHÍNH GỐC ===\n{rag_raw_text}\n==================================\n"

        crew = Crew(
            agents=agents_list,
            tasks=gathering_tasks + [t_compose],
            verbose=True,
            memory=False,
            process=Process.sequential, 
            step_callback=self._step_callback
        )

        result = crew.kickoff()
        final_report = result.raw

        try:
            agent_outputs = {
                "market": t_market.output.raw if t_market.output else "No Data",
                "tech": t_tech.output.raw if t_tech.output else "No Data",
                "fin": t_fin.output.raw if t_fin.output else "No Data", 
                "rag_raw": rag_raw_text if rag_raw_text else "No PDF Data"
            }

            eval_manager.save_granular_session(
                session_id=self.session_id,
                ticker=self.symbol,
                query=f"Phân tích tổng hợp cổ phiếu {self.symbol}",
                agent_outputs=agent_outputs,
                final_report=final_report
            )
        except Exception as e:
            print(f"⚠️ Lỗi khi lưu Eval Data: {e}")

        return final_report


class SmartChatbot:
    def __init__(self, session_id, symbol, context_report, history, status_callback=None):
        self.symbol = symbol
        self.context_report = context_report
        self.history = history
        self.status_callback = status_callback

    def _emit(self, msg):
        if self.status_callback: self.status_callback(msg)

    def reply(self, user_query, rag_info=None):
        rag_section = ""
        if rag_info and "NO_DATA" not in rag_info:
            rag_section = f"THÔNG TIN TỪ TÀI LIỆU GỐC (Ưu tiên 1):\n{rag_info}\n"
        
        recent_history = self.history[-4:] if self.history else []
        history_text = ""
        for msg in recent_history:
            role = "USER" if msg['role'] == 'user' else "AI"
            history_text += f"- {role}: {msg['content']}\n"

        report_context = ""
        if self.context_report:
            report_context = f"BÁO CÁO PHÂN TÍCH TRƯỚC ĐÓ (Tham khảo):\n{self.context_report[:1000]}...\n"

        system_prompt = f"""
        Bạn là FinAI, trợ lý tài chính thông minh.

        === LỊCH SỬ HỘI THOẠI (Để hiểu ngữ cảnh 'ông ấy', 'công ty này' là ai) ===
        {history_text}
        ========================================================================

        === DỮ LIỆU TRA CỨU ===
        Mã đang xem: {self.symbol}
        {rag_section}
        {report_context}
        
        === YÊU CẦU CỦA NGƯỜI DÙNG ===
        Câu hỏi: "{user_query}"

        === HƯỚNG DẪN TRẢ LỜI ===
        1. RÀ SOÁT LỊCH SỬ: Nếu câu hỏi dùng đại từ (ông ấy, bà ấy, nó, công ty đó...), hãy nhìn vào 'LỊCH SỬ HỘI THOẠI' để xác định chủ thể.
        2. KIẾN THỨC CHUNG: Nếu câu hỏi về tiểu sử, quê quán, địa lý, hoặc kiến thức xã hội (không phải số liệu tài chính), HÃY DÙNG KIẾN THỨC CÓ SẴN CỦA BẠN. Đừng phụ thuộc vào 'Báo cáo phân tích' hay 'Dữ liệu tra cứu' nếu chúng không chứa thông tin này.
        3. SỐ LIỆU: Chỉ dùng 'DỮ LIỆU TRA CỨU' nếu hỏi về doanh thu, lợi nhuận, chỉ số tài chính.
        4. TRẢ LỜI: Ngắn gọn, đi thẳng vào vấn đề. Nếu không biết thì nói không biết, đừng bịa đặt từ báo cáo không liên quan.
        """

        model = genai.GenerativeModel('gemini-2.5-flash') 
        response = model.generate_content(system_prompt)
        return response.text

def run_analysis_workflow(user_query, session_id, file_path=None, status_callback=None):
    db.create_session(session_id)
    session_data = db.get_session_data(session_id)
    
    current_ticker = session_data['current_ticker']
    context_report = session_data['context_report']
    has_context = bool(context_report)

    if not db.get_messages(session_id):
        db.update_session_metadata(session_id, title=user_query[:40])

    intent = get_user_intent(user_query, has_context)
    target_ticker = intent['ticker'] if intent['ticker'] else current_ticker

    if target_ticker:
        target_ticker = str(target_ticker).upper().strip()

    if not target_ticker: target_ticker = "VNINDEX"
    
    final_file_path = file_path if file_path else intent.get('file_path')
    
    should_run_crew = (intent['type'] == "analyze_stock") or final_file_path

    final_response = ""

    if should_run_crew:
        db.update_session_metadata(session_id, current_ticker=target_ticker)
        crew = FinancialCrew(session_id, target_ticker, final_file_path, status_callback)
        final_response = crew.run()
        db.update_session_metadata(session_id, context_report=final_response)
    else:
        if target_ticker != current_ticker:
             db.update_session_metadata(session_id, current_ticker=target_ticker)
        
        rag_info = None
        if intent['type'] == "chat_with_rag" and target_ticker:
            if status_callback: status_callback(f"🔍 Tra cứu số liệu {target_ticker}...")
            rag_info = rag_engine.query_data(target_ticker, user_query, is_deep_analysis=False)

        if status_callback: status_callback("⚡ Đang trả lời...")
        
        messages = db.get_messages(session_id)
        history = [{'role': m['role'], 'content': m['content']} for m in messages]
        
        bot = SmartChatbot(session_id, target_ticker, context_report, history, status_callback)
        final_response = bot.reply(user_query, rag_info)

    db.add_message(session_id, "user", user_query)
    db.add_message(session_id, "assistant", final_response)
    
    return final_response, None

def generate_report_for_ticker(ticker: str):
    return run_analysis_workflow(f"Phân tích {ticker}", session_id="auto_report")[0], None

if __name__ == "__main__":
    print("## FinAI System ##")
    q = input("Nhập: ")
    res, _ = run_analysis_workflow(q, "cli_test")
    print(res)