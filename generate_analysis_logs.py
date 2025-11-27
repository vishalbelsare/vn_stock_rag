# generate_analysis_logs.py
import os
import sys
import glob
import time
from main import run_analysis_workflow

TARGET_TICKERS = ["ACB", "BCM", "BID", "CTG", "DGC"]

print("🧹 Đang dọn dẹp log cũ trong evaluation_storage/...")
files = glob.glob('evaluation_storage/*.json')
for f in files:
    try:
        os.remove(f)
    except:
        pass

print(f"🚀 Bắt đầu chạy quy trình PHÂN TÍCH TỔNG HỢP cho {len(TARGET_TICKERS)} mã...")
print("Lưu ý: Quá trình này sẽ mất khoảng 30-60 giây cho MỖI mã vì phải chạy Full Crew.")

for i, ticker in enumerate(TARGET_TICKERS):
    query = f"Phân tích tổng hợp chi tiết cổ phiếu {ticker} hôm nay"
    
    session_id = f"AUTO_ANALYSIS_{ticker}_{i}"
    
    print(f"\n------------------------------------------------")
    print(f"[{i+1}/{len(TARGET_TICKERS)}] Đang phân tích mã: {ticker}...")
    
    try:
        response, _ = run_analysis_workflow(query, session_id)
        
        print(f"✅ Đã xong {ticker}. Output length: {len(response)} chars.")
        
    except Exception as e:
        print(f"❌ Lỗi khi chạy mã {ticker}: {e}")
    time.sleep(20) 

print("\n🎉 Hoàn tất! Bây giờ bạn hãy chạy 'python evaluate_sub_agents.py'")