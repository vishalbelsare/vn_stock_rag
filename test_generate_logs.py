import json
import os
import sys
import glob
import time
from main import run_analysis_workflow

REPORTS_DIR = "financial_reports"
LOG_DIR = "evaluation_storage"
PERSIST_DIR = "storage_rag"  
DATASET_FILE = "golden_dataset.json"

def scan_pdf_mapping(directory):
    """
    Tự động quét folder và tạo mapping {TICKER: FILE_PATH}
    """
    mapping = {}
    if not os.path.exists(directory):
        print(f"❌ Không tìm thấy thư mục {directory}")
        return mapping

    pdf_files = glob.glob(os.path.join(directory, "*.pdf"))
    print(f"🔍 Đã tìm thấy {len(pdf_files)} file PDF trong thư mục '{directory}'.")
    
    for file_path in pdf_files:
        filename = os.path.basename(file_path)
        try:
            ticker = filename.split('-')[0].strip().upper()
            if len(ticker) >= 3: 
                mapping[ticker] = file_path
        except IndexError:
            print(f"⚠️ Bỏ qua file sai định dạng tên: {filename}")
            
    return mapping

PDF_MAPPING = scan_pdf_mapping(REPORTS_DIR)
if not PDF_MAPPING:
    print("❌ Không tìm thấy file PDF nào hợp lệ.")
    sys.exit(1)

def detect_ticker_from_query(query):
    query_upper = query.upper()
    matched_ticker = None
    for ticker in PDF_MAPPING.keys():
        if ticker in query_upper:
            if matched_ticker is None or len(ticker) > len(matched_ticker):
                matched_ticker = ticker
    return matched_ticker

files = glob.glob(os.path.join(LOG_DIR, '*.json'))
for f in files: 
    try: os.remove(f) 
    except: pass
print(f"🧹 Đã dọn dẹp log chat cũ trong {LOG_DIR}/.")

try:
    with open(DATASET_FILE, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    print(f"📖 Đã load {len(dataset)} câu hỏi từ {DATASET_FILE}")
except FileNotFoundError:
    print(f"❌ Không tìm thấy file {DATASET_FILE}")
    sys.exit(1)

print("-" * 60)
print(f"🚀 BẮT ĐẦU TEST TỰ ĐỘNG")
print("⚡ Chế độ: Tiết kiệm Quota (Ưu tiên dùng dữ liệu đã lưu trong storage_rag)")
print("-" * 60)

newly_ingested_tickers = set()

for i, item in enumerate(dataset):
    query = item['query']
    ticker = detect_ticker_from_query(query)
    
    print(f"\n[{i+1}/{len(dataset)}] Query: {query}")
    
    current_pdf = None
    
    if ticker:
        ticker_storage_path = os.path.join(PERSIST_DIR, ticker)
        
        if os.path.exists(ticker_storage_path):
            print(f"💾 [Disk Cache] Tìm thấy dữ liệu vector của [{ticker}]. Bỏ qua nạp PDF.")
            current_pdf = None 
            
        elif ticker in PDF_MAPPING:
            if ticker not in newly_ingested_tickers:
                print(f"📥 [Ingest] Chưa có dữ liệu. Đang nạp file: {os.path.basename(PDF_MAPPING[ticker])}")
                current_pdf = PDF_MAPPING[ticker]
                newly_ingested_tickers.add(ticker)
                
                if len(newly_ingested_tickers) > 1:
                    print("⏳ Nghỉ 5s để bảo vệ API Key...")
                    time.sleep(5)
            else:
                print(f"ℹ️ [Session] Mã [{ticker}] đang được xử lý.")
        else:
            print(f"⚠️ Cảnh báo: Mã {ticker} không có file PDF và cũng không có dữ liệu cũ.")
    else:
        print("⚠️ Không nhận diện được mã cổ phiếu.")

    session_id = f"TEST_AUTO_{ticker if ticker else 'UNKNOWN'}_{i}"
    
    try:
        response, _ = run_analysis_workflow(query, session_id, file_path=current_pdf)
        
        preview = response.replace('\n', ' ')[:100]
        print(f"🤖 Bot: {preview}...") 
        
        if "NO_DATA" in response or "không tìm thấy" in response.lower():
            print("⚠️ CẢNH BÁO: Bot không trả lời được!")
            
        time.sleep(5)
            
    except Exception as e:
        print(f"❌ Lỗi hệ thống: {e}")

print("\n✅ HOÀN TẤT QUÁ TRÌNH TEST.")
print("👉 Hãy chạy 'python evaluate_rag.py' để xem điểm số.")