import json
import os
import sys
import glob
import time
from main import run_analysis_workflow

LIMIT_TICKERS = 5  
REPORTS_DIR = "financial_reports"
LOG_DIR = "evaluation_storage"
PERSIST_DIR = "storage_rag"
DATASET_FILE = "golden_dataset.json"

def get_target_mapping(directory, limit):
    if not os.path.exists(directory):
        print(f"❌ Không tìm thấy {directory}")
        return {}

    pdf_files = glob.glob(os.path.join(directory, "*.pdf"))
    temp_map = {}
    
    for file_path in pdf_files:
        filename = os.path.basename(file_path)
        try:
            ticker = filename.split('-')[0].strip().upper()
            if len(ticker) >= 3:
                temp_map[ticker] = file_path
        except:
            pass
    
    sorted_tickers = sorted(list(temp_map.keys()))[:limit]
    
    final_map = {k: temp_map[k] for k in sorted_tickers}
    return final_map, sorted_tickers

PDF_MAPPING, TARGET_LIST = get_target_mapping(REPORTS_DIR, LIMIT_TICKERS)

if not PDF_MAPPING:
    print("❌ Không tìm thấy file PDF.")
    sys.exit(1)

print("-" * 60)
print(f"🚀 CHẾ ĐỘ TEST GIỚI HẠN: {len(TARGET_LIST)} MÃ")
print(f"📋 Danh sách mã: {', '.join(TARGET_LIST)}")
print("-" * 60)

def detect_ticker_from_query(query):
    query_upper = query.upper()
    matched_ticker = None
    for ticker in TARGET_LIST:
        if ticker in query_upper:
            if matched_ticker is None or len(ticker) > len(matched_ticker):
                matched_ticker = ticker
    return matched_ticker

files = glob.glob(os.path.join(LOG_DIR, '*.json'))
for f in files: 
    try: os.remove(f) 
    except: pass
print(f"🧹 Đã dọn dẹp log cũ.")

try:
    with open(DATASET_FILE, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
except:
    print("❌ Lỗi đọc dataset.")
    sys.exit(1)

count_run = 0
for i, item in enumerate(dataset):
    query = item['query']
    ticker = detect_ticker_from_query(query)
    
    if not ticker:
        continue
        
    count_run += 1
    print(f"\n[{count_run}] Query ({ticker}): {query}")
    
    current_pdf = None
    ticker_storage_path = os.path.join(PERSIST_DIR, ticker)
    
    if os.path.exists(ticker_storage_path):
        print(f"💾 [Cache] Dùng dữ liệu cũ trong ổ cứng.")
        current_pdf = None
    else:
        print(f"📥 [Ingest] Nạp mới file PDF...")
        current_pdf = PDF_MAPPING[ticker]
        time.sleep(5) 

    session_id = f"TEST_LIMIT_{ticker}_{i}"
    
    try:
        response, _ = run_analysis_workflow(query, session_id, file_path=current_pdf)
        print(f"🤖 Bot: {response.replace(chr(10), ' ')[:100]}...")
        time.sleep(1)
    except Exception as e:
        print(f"❌ Lỗi: {e}")

print(f"\n✅ Đã chạy xong {count_run} câu hỏi cho {len(TARGET_LIST)} mã.")
print("👉 Chạy 'python evaluate_rag.py' để xem kết quả mới.")