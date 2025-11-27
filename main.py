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
    try:
        # print(f"🔍 Gemini đang phân tích ý định: '{user_query}'...")
        
        api_key = key_manager.get_next_key()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        context_info = "Đã có ngữ cảnh hội thoại trước đó." if has_context else "Cuộc hội thoại mới."

        prompt = f"""
        Bạn là bộ định tuyến (Router) thông minh cho hệ thống chứng khoán Việt Nam.
        
        INPUT:
        - Ngữ cảnh: {context_info}
        - Câu hỏi: "{user_query}"

        NHIỆM VỤ:
        1. "analyze_stock": Khi người dùng yêu cầu phân tích, đánh giá, nhận định, xem biểu đồ, viết báo cáo.
        2. "chat_with_rag": Khi hỏi chi tiết số liệu cụ thể (Doanh thu bao nhiêu, Lợi nhuận thế nào, Tài sản...).
        3. "chat_direct": Hỏi thông tin chung, xã giao, chào hỏi.

        Trích xuất Ticker (nếu có). Chuyển tên công ty về mã 3 chữ cái (VD: Vinamilk -> VNM).

        OUTPUT JSON:
        {{ "type": "analyze_stock" | "chat_with_rag" | "chat_direct", "ticker": "MÃ_CK" | null, "file_path": null }}
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
    def __init__(self, session_id, symbol, status_callback=None, rag_data_text=None):
        self.session_id = session_id
        self.symbol = symbol
        self.status_callback = status_callback 
        self.rag_data_text = rag_data_text # Dữ liệu RAG đã lấy từ bên ngoài truyền vào
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
        self._emit(f"🚀 Bắt đầu phân tích toàn diện {self.symbol}...")

        # Khởi tạo Agents
        market_agent = self.agents.market_news_analyst()
        tech_agent = self.agents.technical_analyst()
        fin_agent = self.agents.financial_competitor_analyst() 
        editor_agent = self.agents.report_editor()

        # Khởi tạo Tasks
        t_market = self.tasks.market_news_analysis(market_agent)
        t_tech = self.tasks.technical_analysis(tech_agent, self.symbol)
        t_fin = self.tasks.financial_competitor_analysis(fin_agent, self.symbol)
        
        gathering_tasks = [t_market, t_tech, t_fin]
        agents_list = [market_agent, tech_agent, fin_agent, editor_agent]

        has_rag_data = bool(self.rag_data_text)

        t_compose = self.tasks.compose_newsletter(
            editor_agent, 
            context=gathering_tasks, 
            symbol=self.symbol, 
            chat_history=self.history,
            has_rag_data=has_rag_data
        )
        
        # Inject RAG data vào Task cuối cùng
        if self.rag_data_text:
            t_compose.description += f"\n\n=== DỮ LIỆU TỪ BÁO CÁO TÀI CHÍNH GỐC ===\n{self.rag_data_text}\n==================================\n"

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

        # Ghi log đánh giá
        try:
            agent_outputs = {
                "market": t_market.output.raw if t_market.output else "No Data",
                "tech": t_tech.output.raw if t_tech.output else "No Data",
                "fin": t_fin.output.raw if t_fin.output else "No Data", 
                "rag_raw": self.rag_data_text if self.rag_data_text else "No PDF Data"
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
        self.session_id = session_id

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

        === LỊCH SỬ HỘI THOẠI ===
        {history_text}
        
        === DỮ LIỆU THAM KHẢO ===
        Mã đang xem: {self.symbol}
        {rag_section}
        {report_context}
        
        === CÂU HỎI CỦA USER ===
        "{user_query}"

        === YÊU CẦU ===
        Trả lời ngắn gọn, đi thẳng vào vấn đề. Nếu có dữ liệu từ 'Tài liệu gốc', hãy ưu tiên dùng nó.
        """

        # Dùng Flash cho Chat nhanh
        model = genai.GenerativeModel('gemini-2.5-flash') 
        response = model.generate_content(system_prompt)
        
        if rag_info:
             eval_manager.save_granular_session(
                session_id=self.session_id,
                ticker=self.symbol,
                query=user_query,
                agent_outputs={"rag_raw": rag_info}, 
                final_report=response.text
            )
            
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
    if target_ticker: target_ticker = str(target_ticker).upper().strip()
    
    if not target_ticker: 
        target_ticker = current_ticker if current_ticker else "VNINDEX"

    final_file_path = file_path if file_path else intent.get('file_path')
    if final_file_path:
        if status_callback: status_callback(f"📑 Đang đọc tài liệu {target_ticker}...")
        try: 
            rag_engine.ingest_pdf(final_file_path, target_ticker)
        except Exception as e: 
            print(f"Ingest Err: {e}")

    has_existing_data = False
    if target_ticker:
        persist_path = os.path.join("storage_rag", target_ticker)
        if os.path.exists(persist_path):
            has_existing_data = True

    should_run_crew = (intent['type'] == "analyze_stock")

    final_response = ""

    if should_run_crew:
        db.update_session_metadata(session_id, current_ticker=target_ticker)
        
        rag_raw_text = ""
        if has_existing_data:
             if status_callback: status_callback("🔍 Trích xuất dữ liệu BCTC...")
             query_rag = f"Trích xuất số liệu {target_ticker}: Doanh thu, Lợi nhuận, Tổng tài sản, Nợ, Dòng tiền."
             rag_raw_text = rag_engine.query_data(target_ticker, query_rag, is_deep_analysis=True)

        crew = FinancialCrew(session_id, target_ticker, status_callback, rag_raw_text)
        final_response = crew.run()
        db.update_session_metadata(session_id, context_report=final_response)
    
    else:
        if target_ticker != current_ticker:
             db.update_session_metadata(session_id, current_ticker=target_ticker)
        
        rag_info = None
        
        if (intent['type'] == "chat_with_rag" or final_file_path or has_existing_data):
            if status_callback: status_callback(f"🔍 Tra cứu số liệu {target_ticker}...")
            rag_info = rag_engine.query_data(target_ticker, user_query, is_deep_analysis=False)
            print(f"DEBUG RAG OUTPUT: {rag_info}") # <--- In ra để debug

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