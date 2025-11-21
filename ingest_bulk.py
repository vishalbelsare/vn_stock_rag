from dotenv import load_dotenv
load_dotenv()
import os
import time
import threading
import concurrent.futures
import logging
import sys

import nltk
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

from llama_index.core import VectorStoreIndex, Document
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini

os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

from key_manager import key_manager


REPORTS_DIR = "financial_reports"
PERSIST_DIR = "./storage_rag"
MAX_WORKERS = 8  

print_lock = threading.Lock()

def safe_print(msg):
    with print_lock:
        print(msg)

def get_ticker_from_filename(filename):
    try:
        base_name = filename.split('.')[0] 
        ticker = base_name.split('-')[0].strip().upper()
        if 3 <= len(ticker) <= 4:
            return ticker
        return None
    except:
        return None

def ingest_worker(file_info):
    filename, file_path = file_info
    ticker = get_ticker_from_filename(filename)

    if not ticker:
        safe_print(f"⚠️ Bỏ qua: {filename}")
        return

    try:
        api_key = key_manager.get_next_key()
    except Exception as e:
        safe_print(f"❌ Hết key: {e}")
        return

    try:
        embed_model = GeminiEmbedding(
            model_name="models/text-embedding-004", 
            api_key=api_key
        )
        llm = Gemini(
            model_name="models/gemini-2.5-pro", 
            api_key=api_key
        )

        with open(file_path, "r", encoding="utf-8") as f:
            text_content = f.read()
        
        if not text_content:
            safe_print(f"⚠️ File rỗng: {filename}")
            return

        doc = Document(text=text_content, metadata={"ticker": ticker, "source": filename})
        
        index = VectorStoreIndex.from_documents(
            [doc],
            embed_model=embed_model,
            llm=llm
        )

        ticker_persist_dir = os.path.join(PERSIST_DIR, ticker)
        if not os.path.exists(ticker_persist_dir):
            os.makedirs(ticker_persist_dir, exist_ok=True)
            
        index.storage_context.persist(persist_dir=ticker_persist_dir)
        
        safe_print(f"✅ [Key ...{api_key[-4:]}] Đã xong: {ticker}")

    except Exception as e:
        safe_print(f"❌ Lỗi {ticker}: {e}")

def run_parallel_ingestion():
    if not os.path.exists(REPORTS_DIR):
        print(f"Không tìm thấy thư mục {REPORTS_DIR}")
        return

    all_files = os.listdir(REPORTS_DIR)
    text_files = [f for f in all_files if f.endswith('.ocr_text.txt')]
    
    if not text_files:
        print("❌ Không tìm thấy file .ocr_text.txt nào.")
        return

    work_items = []
    for f in text_files:
        path = os.path.join(REPORTS_DIR, f)
        work_items.append((f, path))

    print(f"🚀 Bắt đầu nạp {len(work_items)} file với {MAX_WORKERS} luồng...")
    
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(ingest_worker, work_items)

    end_time = time.time()
    print(f"\n🎉 HOÀN TẤT! Thời gian: {end_time - start_time:.2f}s")

if __name__ == "__main__":
    run_parallel_ingestion()