# evaluation_manager.py
import os
import json
import uuid
from datetime import datetime

EVAL_DIR = "evaluation_storage"
os.makedirs(EVAL_DIR, exist_ok=True)

class EvaluationManager:
    def save_granular_session(self, session_id, ticker, query, agent_outputs, final_report):
        """
        Lưu dữ liệu chi tiết từng Agent để đánh giá riêng biệt (Component-wise Eval).
        
        Args:
            agent_outputs (dict): Dictionary chứa kết quả của từng sub-agent.
                                  Ví dụ: {'market': '...', 'tech': '...'}
            final_report (str): Kết quả cuối cùng của Editor.
        """
        
        record = {
            "meta": {
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "ticker": ticker,
                "user_query": query
            },
            "sub_agents_retrieval": {
                "market_news": agent_outputs.get('market'),     
                "technical": agent_outputs.get('tech'),         
                "financial_competitor": agent_outputs.get('fin'), 
                "internal_rag": agent_outputs.get('rag_raw')    
            },
            "final_generation": {
                "context_provided": list(agent_outputs.values()), 
                "answer": final_report                            
            }
        }

        safe_ticker = ticker.replace(" ", "")
        filename = f"{safe_ticker}_FULL_{int(datetime.now().timestamp())}.json"
        file_path = os.path.join(EVAL_DIR, filename)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(record, f, ensure_ascii=False, indent=4)
            print(f"✅ [Eval] Đã lưu dữ liệu chi tiết vào: {file_path}")
        except Exception as e:
            print(f"❌ [Eval] Lỗi lưu file: {e}")

eval_manager = EvaluationManager()