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

from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini

from key_manager import key_manager
from tools.ocr_tool import MistralOCRTool 

# Tắt log rác
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
logging.getLogger('llama_index').setLevel(logging.WARNING)

REPORTS_DIR = "financial_reports"
PERSIST_DIR = "./storage_rag"
MAX_WORKERS = 2

print_lock = threading.Lock()

def safe_print(msg):
    with print_lock:
        print(msg)

def get_ticker_from_filename(filename):
    """
    Lấy mã ticker từ tên file. 
    Ví dụ: 'ACB-Q3.pdf' -> 'ACB'
    """
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
        safe_print(f"⚠️ [Bỏ qua] Không tìm thấy mã cổ phiếu trong tên file: {filename}")
        return

    try:
        gemini_api_key = key_manager.get_next_key()
    except Exception as e:
        safe_print(f"❌ Hết Google API key: {e}")
        return

    ocr_tool = MistralOCRTool()

    try:
        base_name = os.path.splitext(filename)[0]
        txt_filename = f"{base_name}.ocr_text.txt"
        txt_path = os.path.join(REPORTS_DIR, txt_filename)
        
        text_content = ""

        if os.path.exists(txt_path):
            safe_print(f"ℹ️ [Cache] Đã có file text cho {ticker}, bỏ qua OCR.")
            with open(txt_path, "r", encoding="utf-8") as f:
                text_content = f.read()
        else:
            safe_print(f"📖 [OCR] Đang xử lý file PDF: {filename}...")
            ocr_tool._run(file_path)
            
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    text_content = f.read()
            else:
                safe_print(f"❌ [Lỗi OCR] Không tạo được file text cho {filename}")
                return

        if not text_content:
            safe_print(f"⚠️ [Cảnh báo] Nội dung rỗng sau khi OCR: {filename}")
            return

        safe_print(f"⚙️ [Embedding] Đang vector hóa {ticker} (Dùng key ...{gemini_api_key[-4:]})...")

        embed_model = GeminiEmbedding(
            model_name="models/text-embedding-004", 
            api_key=gemini_api_key
        )
        llm = Gemini(
            model_name="models/gemini-2.5-pro", 
            api_key=gemini_api_key
        )
        
        Settings.llm = llm
        Settings.embed_model = embed_model
        Settings.chunk_size = 4096
        Settings.chunk_overlap = 512

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
        
        safe_print(f"✅ [Hoàn tất] Đã nạp thành công: {ticker}")

    except Exception as e:
        safe_print(f"❌ [Lỗi] Xử lý {ticker} thất bại: {e}")

def run_parallel_ingestion():
    if not os.path.exists(REPORTS_DIR):
        print(f"❌ Không tìm thấy thư mục {REPORTS_DIR}")
        return

    all_files = os.listdir(REPORTS_DIR)
    pdf_files = [f for f in all_files if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("❌ Không tìm thấy file .pdf nào trong thư mục financial_reports.")
        return

    work_items = []
    for f in pdf_files:
        path = os.path.join(REPORTS_DIR, f)
        work_items.append((f, path))

    print(f"🚀 Tìm thấy {len(work_items)} file PDF. Bắt đầu xử lý với {MAX_WORKERS} luồng...")
    print(f"⚠️ Lưu ý: Đảm bảo bạn đã cấu hình MISTRAL_API_KEY trong file .env")
    
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(ingest_worker, work_items)

    end_time = time.time()
    print(f"\n🎉 HOÀN TẤT TOÀN BỘ! Tổng thời gian: {end_time - start_time:.2f}s")

if __name__ == "__main__":
    run_parallel_ingestion()