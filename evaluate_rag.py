from dotenv import load_dotenv
load_dotenv() 

import os
import json
import time
import pandas as pd
import asyncio
from typing import Any, List, Optional
from datasets import Dataset

os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

from ragas import evaluate, RunConfig
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult, ChatGeneration 
from langchain_core.embeddings import Embeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded, ServiceUnavailable
from google.generativeai.types.safety_types import HarmBlockThreshold, HarmCategory

from key_manager import key_manager

EVAL_STORAGE_DIR = "evaluation_storage"
OUTPUT_FILE = "rag_evaluation_report.csv"

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

class MultiKeyGeminiLLM(BaseChatModel):
    model_name: str = "gemini-2.5-flash"
    temperature: float = 0
    request_timeout: int = 60

    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        return self._rotate_and_call_sync(messages)

    async def _agenerate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        return await self._rotate_and_call_async(messages)

    def _rotate_and_call_sync(self, messages):
        for attempt in range(2): 
            max_retries = 15
            for i in range(max_retries):
                try:
                    current_key = key_manager.get_next_key()
                    client = ChatGoogleGenerativeAI(
                        model=self.model_name,
                        google_api_key=current_key,
                        temperature=self.temperature,
                        safety_settings=SAFETY_SETTINGS,
                        transport="rest",
                        max_retries=1,
                        request_timeout=self.request_timeout
                    )
                    
                    response = client.invoke(messages)
                    return ChatResult(generations=[ChatGeneration(message=response)])

                except (ResourceExhausted, ServiceUnavailable, DeadlineExceeded):
                    time.sleep(2)
                    continue
                except Exception as e:
                    print(f"⚠️ Sync Error: {e}")
                    time.sleep(1)
                    continue
            
            if attempt == 0:
                print("💤 Hết quota tạm thời. Dừng 30s...")
                time.sleep(30)

        return ChatResult(generations=[ChatGeneration(message=BaseMessage(content='{"score": 0.0}', type="ai"))])

    async def _rotate_and_call_async(self, messages):
        for attempt in range(2):
            max_retries = 15
            for i in range(max_retries):
                try:
                    current_key = key_manager.get_next_key()
                    client = ChatGoogleGenerativeAI(
                        model=self.model_name,
                        google_api_key=current_key,
                        temperature=self.temperature,
                        safety_settings=SAFETY_SETTINGS,
                        transport="rest",
                        max_retries=1,
                        request_timeout=self.request_timeout
                    )
                    
                    response = await client.ainvoke(messages)
                    return ChatResult(generations=[ChatGeneration(message=response)])

                except (ResourceExhausted, ServiceUnavailable, DeadlineExceeded):
                    await asyncio.sleep(2)
                    continue
                except Exception as e:
                    print(f"⚠️ Async Error: {e}")
                    await asyncio.sleep(1)
                    continue
            
            if attempt == 0:
                print("💤 Async Hết quota. Ngủ 30s...")
                await asyncio.sleep(30)

        return ChatResult(generations=[ChatGeneration(message=BaseMessage(content='{"score": 0.0}', type="ai"))])

    @property
    def _llm_type(self) -> str:
        return "google-gemini-multikey"

class MultiKeyEmbeddings(Embeddings):
    model_name: str = "models/text-embedding-004"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._rotate_call(texts, is_doc=True)

    def embed_query(self, text: str) -> List[float]:
        return self._rotate_call(text, is_doc=False)

    def _rotate_call(self, input_data, is_doc=True):
        for _ in range(10):
            try:
                current_key = key_manager.get_next_key()
                client = GoogleGenerativeAIEmbeddings(
                    model=self.model_name,
                    google_api_key=current_key,
                    transport="rest", 
                    request_timeout=60
                )
                if is_doc: return client.embed_documents(input_data)
                return client.embed_query(input_data)
            except Exception:
                time.sleep(1)
                continue
        return [[0.0]*768] if is_doc else [0.0]*768

def load_evaluation_data():
    if not os.path.exists(EVAL_STORAGE_DIR): return None
    data_files = [f for f in os.listdir(EVAL_STORAGE_DIR) if f.endswith('.json')]
    if not data_files: return None

    print(f"📂 Đã tải {len(data_files)} file báo cáo.")
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
                    ctx_list.append(f"[{agent}]: {content}")
            if not ctx_list: ctx_list = ["No context available"]

            gt = record.get('ground_truth', a)

            questions.append(q)
            answers.append(a)
            contexts.append(ctx_list)
            ground_truths.append(gt)
            session_ids.append(record['meta']['session_id'])
        except Exception: continue

    return Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }), session_ids

def run_evaluation():
    print("\n🚀 KÍCH HOẠT CHẾ ĐỘ ĐÁNH GIÁ (FIX AIMessage ERROR)")
    
    judge_llm = MultiKeyGeminiLLM()
    judge_embeddings = MultiKeyEmbeddings()

    result = load_evaluation_data()
    if not result: return
    dataset, session_ids = result

    NUM_WORKERS = 2
    
    print(f"📊 Số lượng: {len(dataset)}")
    print("⏳ Đang chấm điểm...")

    try:
        evaluation_results = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=judge_llm,
            embeddings=judge_embeddings,
            run_config=RunConfig(
                max_workers=NUM_WORKERS, 
                timeout=600,
                max_retries=5
            ),
            raise_exceptions=False 
        )
        
        print("\n✅ HOÀN TẤT!")
        print(evaluation_results)

        df = evaluation_results.to_pandas()
        df.insert(0, "Session_ID", session_ids)
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"\n📄 Kết quả: {os.path.abspath(OUTPUT_FILE)}")
        
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")

if __name__ == "__main__":
    run_evaluation()