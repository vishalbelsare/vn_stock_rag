import os
import json
import pandas as pd
from datasets import Dataset
from ragas import evaluate, RunConfig
from ragas.metrics import faithfulness, answer_relevancy
from evaluate_rag import MultiKeyGeminiLLM, MultiKeyEmbeddings 

EVAL_STORAGE_DIR = "evaluation_storage"
OUTPUT_FILE = "editor_faithfulness_report.csv"

def load_editor_data():
    files = [f for f in os.listdir(EVAL_STORAGE_DIR) if f.endswith('.json')]
    
    questions, answers, contexts, session_ids = [], [], [], []

    for file in files:
        try:
            with open(os.path.join(EVAL_STORAGE_DIR, file), 'r', encoding='utf-8') as f:
                record = json.load(f)
            
            sub_agents = record['sub_agents_retrieval']
            
            # Chỉ lấy các file Log có chạy đủ Agent (loại bỏ log chỉ chạy RAG đơn lẻ)
            if not sub_agents.get('technical') or sub_agents.get('technical') == "No Data":
                continue

            # Context cho Editor chính là Output của các Sub-Agents
            # Chúng ta nối chuỗi lại để Ragas hiểu đây là "Tài liệu tham khảo"
            combined_context = []
            if sub_agents.get('market_news'): 
                combined_context.append(f"[MARKET REPORT]: {sub_agents['market_news']}")
            if sub_agents.get('technical'): 
                combined_context.append(f"[TECHNICAL REPORT]: {sub_agents['technical']}")
            if sub_agents.get('financial_competitor'): 
                combined_context.append(f"[FINANCIAL REPORT]: {sub_agents['financial_competitor']}")
            if sub_agents.get('internal_rag') and len(sub_agents['internal_rag']) > 50:
                combined_context.append(f"[RAG DATA]: {sub_agents['internal_rag']}")

            questions.append(record['meta']['user_query'])
            answers.append(record['final_generation']['answer'])
            contexts.append(combined_context)
            session_ids.append(record['meta']['session_id'])

        except Exception:
            continue
    
    if not questions: return None
    
    return Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts
    }), session_ids

def run_editor_eval():
    print("🚀 BẮT ĐẦU ĐÁNH GIÁ EDITOR (FAITHFULNESS)...")
    
    result = load_editor_data()
    if not result:
        print("❌ Không tìm thấy dữ liệu log của Full Crew.")
        return

    dataset, session_ids = result
    print(f"📊 Số lượng báo cáo cần chấm: {len(dataset)}")

    judge_llm = MultiKeyGeminiLLM()
    judge_embeddings = MultiKeyEmbeddings()

    try:
        metrics = [faithfulness, answer_relevancy]

        results = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=judge_llm,
            embeddings=judge_embeddings,
            run_config=RunConfig(max_workers=2, timeout=600),
            raise_exceptions=False
        )

        print("\n✅ KẾT QUẢ ĐÁNH GIÁ EDITOR:")
        print(results)
        
        df = results.to_pandas()
        df.insert(0, "Session_ID", session_ids)
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"\n📄 File chi tiết: {OUTPUT_FILE}")

    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    run_editor_eval()