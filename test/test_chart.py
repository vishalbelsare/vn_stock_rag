# test/run_test_charting_tool.py
import os
import sys
import time
import glob
from datetime import datetime

# Đảm bảo project root được thêm vào sys.path
THIS_DIR = os.path.dirname(os.path.abspath(__file__))       # .../project/test
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..")) # .../project
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# bây giờ import tool
try:
    from tools.charting_tool import ChartingTool, CHARTS_DIR_FULL_PATH
except Exception as e:
    print("ERROR: Không thể import ChartingTool từ tools/charting_tool.py")
    print("Chi tiết lỗi:", e)
    sys.exit(2)

def find_latest_chart(ticker, charts_dir):
    pattern = os.path.join(charts_dir, f"{ticker}_*.png")
    files = glob.glob(pattern)
    if not files:
        return None
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def main(tickers):
    tool = ChartingTool()
    ok = True
    for t in tickers:
        print("="*60)
        print("Testing:", t)
        start = time.time()
        try:
            md = tool._run(t)
        except Exception as e:
            import traceback; traceback.print_exc()
            ok = False
            continue
        print("Duration:", time.time() - start)
        print("Preview of returned Markdown:")
        print((md[:1000] + "...") if md and len(md) > 1000 else (md or "(empty)"))
        chart = find_latest_chart(t, CHARTS_DIR_FULL_PATH)
        if chart:
            print("Chart file:", chart)
        else:
            print("No chart file found for", t)
            ok = False
    print("="*60)
    print("RESULT:", "OK" if ok else "FAILED")
    return 0 if ok else 1

if __name__ == "__main__":
    tickers = ["HPG", "MWG"]
    raise SystemExit(main(tickers))
