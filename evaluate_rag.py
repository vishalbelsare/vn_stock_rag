from dotenv import load_dotenv
load_dotenv() 

import os
import json
import time
import pandas as pd
import asyncio
from typing import Any, List, Optional
from datasets import Dataset

# Fix lỗi thư viện Ragas khi dùng Gemini
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

from ragas import evaluate, RunConfig
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness
)
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult, ChatGeneration 
from langchain_core.embeddings import Embeddings
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded, ServiceUnavailable

from key_manager import key_manager

EVAL_STORAGE_DIR = "evaluation_storage"
OUTPUT_FILE = "rag_evaluation_report.csv"
GOLDEN_DATASET_FILE = "golden_dataset.json"

class MultiKeyGeminiLLM(BaseChatModel):
    model_name: str = "gemini-2.5-flash" 
    temperature: float = 0

    def _generate(
        self, 
        messages: List[BaseMessage], 
        stop: Optional[List[str]] = None, 
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any
    ) -> ChatResult:
        
        for _ in range(3):
            try:
                current_key = key_manager.get_next_key()
                client = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=current_key,
                    temperature=self.temperature
                )
                response = client.invoke(messages)
                return ChatResult(generations=[ChatGeneration(message=response)])
            except Exception as e:
                print(f"⚠️ Eval LLM Error (Sync): {e}, Retrying...")
                time.sleep(10)
        return ChatResult(generations=[ChatGeneration(message=BaseMessage(content='{"score": 0.0}', type="ai"))])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any
    ) -> ChatResult:
        
        for _ in range(3):
            try:
                current_key = key_manager.get_next_key()
                client = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=current_key,
                    temperature=self.temperature
                )
                response = await client.ainvoke(messages)
                return ChatResult(generations=[ChatGeneration(message=response)])
            except Exception as e:
                print(f"⚠️ Eval LLM Error (Async): {e}, Retrying...")
                await asyncio.sleep(10)
        return ChatResult(generations=[ChatGeneration(message=BaseMessage(content='{"score": 0.0}', type="ai"))])

    @property
    def _llm_type(self) -> str:
        return "google-gemini-multikey"

class MultiKeyEmbeddings(Embeddings):
    model_name: str = "models/text-embedding-004"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        for _ in range(3):
            try:
                current_key = key_manager.get_next_key()
                client = GoogleGenerativeAIEmbeddings(model=self.model_name, google_api_key=current_key)
                return client.embed_documents(texts)
            except Exception:
                time.sleep(5)
        return [[0.0]*768 for _ in texts] 

    def embed_query(self, text: str) -> List[float]:
        for _ in range(3):
            try:
                current_key = key_manager.get_next_key()
                client = GoogleGenerativeAIEmbeddings(model=self.model_name, google_api_key=current_key)
                return client.embed_query(text)
            except Exception:
                time.sleep(5)
        return [0.0]*768 


def load_evaluation_data():
    """Load log từ folder và ghép với Ground Truth"""
    if not os.path.exists(EVAL_STORAGE_DIR):
        print("Chưa có dữ liệu log.")
        return None
    
    ground_truths_map = {}
    if os.path.exists(GOLDEN_DATASET_FILE):
        try:
            with open(GOLDEN_DATASET_FILE, 'r', encoding='utf-8') as f:
                gd = json.load(f)
                for item in gd:
                    ground_truths_map[item['query']] = {
                        "ground_truth": item['ground_truth_answer'],
                        "ground_truth_context": item.get('ground_truth_context', [])
                    }
            print(f"✅ Đã tải Golden Dataset: {len(ground_truths_map)} mẫu.")
        except Exception as e:
            print(f"⚠️ Lỗi đọc Golden Dataset: {e}")

    # Load Logs
    data_files = [f for f in os.listdir(EVAL_STORAGE_DIR) if f.endswith('.json')]
    if not data_files: return None

    questions, answers, contexts, ground_truths, session_ids = [], [], [], [], []

    for file in data_files:
        try:
            with open(os.path.join(EVAL_STORAGE_DIR, file), 'r', encoding='utf-8') as f:
                record = json.load(f)
            
            q = record['meta']['user_query']
            a = record['final_generation']['answer']
            
            sub_agents = record['sub_agents_retrieval']
            ctx_list = []
            for agent, content in sub_agents.items():
                if content and isinstance(content, str) and "No Data" not in content:
                    ctx_list.append(f"[{agent.upper()} REPORT]: {content}")
            
            if not ctx_list: ctx_list = ["No context available"]

            gt = "N/A"
            if q in ground_truths_map:
                gt = ground_truths_map[q]['ground_truth']
            
            questions.append(q)
            answers.append(a)
            contexts.append(ctx_list)
            ground_truths.append(gt) 
            session_ids.append(record['meta']['session_id'])
            
        except Exception as e: 
            print(f"Bỏ qua file {file}: {e}")
            continue

    if not questions: return None

    return Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }), session_ids

def run_evaluation():
    print("\n🚀 KÍCH HOẠT CHẾ ĐỘ ĐÁNH GIÁ RAGAS")
    
    judge_llm = MultiKeyGeminiLLM()
    judge_embeddings = MultiKeyEmbeddings()

    result = load_evaluation_data()
    if not result: 
        print("❌ Không có dữ liệu để đánh giá.")
        return
    dataset, session_ids = result
    
    print(f"📊 Số lượng mẫu đánh giá: {len(dataset)}")
    print("⏳ Đang chấm điểm (có thể mất vài phút)...")

    try:
        metrics = [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
            answer_correctness 
        ]

        evaluation_results = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=judge_llm,
            embeddings=judge_embeddings,
            run_config=RunConfig(max_workers=2, timeout=600), 
            raise_exceptions=False 
        )
        
        print("\n✅ HOÀN TẤT ĐÁNH GIÁ!")
        print(evaluation_results)

        df = evaluation_results.to_pandas()
        df.insert(0, "Session_ID", session_ids)
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"\n📄 Kết quả chi tiết đã lưu tại: {os.path.abspath(OUTPUT_FILE)}")
        
    except Exception as e:
        print(f"\n❌ Lỗi trong quá trình Ragas evaluate: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_evaluation()