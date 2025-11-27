from dotenv import load_dotenv
load_dotenv() 

import os
import json
import pandas as pd
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from key_manager import key_manager

EVAL_STORAGE_DIR = "evaluation_storage"
OUTPUT_FILE = "sub_agents_score_card.csv"

RUBRICS = {
    "market_news": """
    Tiêu chí đánh giá Market News Agent (Thang 1-5):
    - 5 điểm: Có ít nhất 3 tin tức cụ thể, có ngày tháng, có đánh giá tác động rõ ràng.
    - 3 điểm: Có tin tức nhưng chung chung, thiếu ngày tháng hoặc thiếu đánh giá.
    - 1 điểm: Trả về "No Data", tin tức không liên quan hoặc lỗi.
    """,
    "technical": """
    Tiêu chí đánh giá Technical Agent (Thang 1-5):
    - 5 điểm: Có đường dẫn ảnh biểu đồ (![...](path)), có các chỉ số cụ thể (RSI=..., MA=...), có nhận định Mua/Bán rõ ràng.
    - 3 điểm: Có chỉ số nhưng thiếu biểu đồ, hoặc nhận định mập mờ.
    - 1 điểm: Không có số liệu kỹ thuật, không có biểu đồ.
    """,
    "financial_competitor": """
    Tiêu chí đánh giá Competitor Agent (Thang 1-5):
    - 5 điểm: Có bảng so sánh chỉ số (P/E, ROE...) với ít nhất 2 đối thủ, có tin tức về đối thủ.
    - 3 điểm: Có nêu tên đối thủ nhưng thiếu số liệu so sánh cụ thể.
    - 1 điểm: Không tìm thấy đối thủ hoặc số liệu sai định dạng.
    """
}

def evaluate_single_agent(agent_name, content, llm):
    if not content or content == "No Data":
        return 0, "Không có dữ liệu đầu ra."

    rubric = RUBRICS.get(agent_name, "")
    prompt = f"""
    Bạn là Giám khảo đánh giá chất lượng AI.
    
    {rubric}

    Dưới đây là nội dung đầu ra của Agent:
    --------------------
    {content}
    --------------------

    Hãy chấm điểm và đưa ra nhận xét ngắn gọn.
    OUTPUT FORMAT JSON: {{ "score": [số điểm 1-5], "reason": "[lý do ngắn gọn]" }}
    """
    
    try:
        res = llm.invoke(prompt)
        # Clean json string
        text = res.content.replace('```json', '').replace('```', '').strip()
        data = json.loads(text)
        return data['score'], data['reason']
    except Exception as e:
        return 0, f"Lỗi chấm điểm: {str(e)}"

def run_sub_agent_evaluation():
    print("🚀 BẮT ĐẦU ĐÁNH GIÁ CHẤT LƯỢNG TỪNG AGENT...")
    
    # Init LLM
    api_key = key_manager.get_next_key()
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key, temperature=0)

    results = []
    
    files = [f for f in os.listdir(EVAL_STORAGE_DIR) if f.endswith('.json')]
    
    for file in files:
        try:
            with open(os.path.join(EVAL_STORAGE_DIR, file), 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            ticker = data['meta']['ticker']
            session_id = data['meta']['session_id']
            sub_agents = data['sub_agents_retrieval']

            # Chỉ đánh giá các file log của quy trình Phân tích (có đủ agent)
            # Bỏ qua các file log chỉ có RAG đơn lẻ
            if len(sub_agents) < 2: 
                continue

            print(f"Set: {ticker} | ID: {session_id[:8]}...")

            row = {
                "Session_ID": session_id,
                "Ticker": ticker,
                "Timestamp": data['meta']['timestamp']
            }

            # Chấm điểm từng ông
            for agent_key in ["market_news", "technical", "financial_competitor"]:
                content = sub_agents.get(agent_key, "")
                score, reason = evaluate_single_agent(agent_key, content, llm)
                
                row[f"{agent_key}_score"] = score
                row[f"{agent_key}_reason"] = reason
                print(f"  - {agent_key}: {score}/5")
            
            results.append(row)
            time.sleep(1) # Tránh rate limit

        except Exception as e:
            print(f"  ❌ Lỗi file {file}: {e}")

    # Lưu kết quả
    if results:
        df = pd.DataFrame(results)
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"\n✅ Đã lưu bảng điểm Sub-Agents tại: {OUTPUT_FILE}")
        
        # In thống kê
        print("\n--- ĐIỂM TRUNG BÌNH ---")
        print(df[["market_news_score", "technical_score", "financial_competitor_score"]].mean())
    else:
        print("Không tìm thấy dữ liệu phù hợp để đánh giá.")

if __name__ == "__main__":
    run_sub_agent_evaluation()