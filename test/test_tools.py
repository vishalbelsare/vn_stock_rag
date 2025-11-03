# test_tools.py

import os
# Tải biến môi trường (nếu có, mặc dù script này không dùng API key trả phí)
from dotenv import load_dotenv
load_dotenv()

# Import trực tiếp các class Tool từ file của bạn
try:
    from tools.financial_tools import TechDataTool, ComprehensiveFinancialTool
    print(">>> Đã import thành công các Tool từ tools/financial_tools.py")
except ImportError as e:
    print(f"!!! LỖI IMPORT: Không thể import các Tool. Hãy kiểm tra lại file. Lỗi: {e}")
    exit()

def run_tech_tool_test(ticker):
    """Hàm để kiểm tra TechDataTool."""
    print("\n" + "="*50)
    print(f"BẮT ĐẦU KIỂM TRA: TechDataTool với mã '{ticker}'")
    print("="*50)
    
    try:
        # 1. Khởi tạo tool
        tech_tool = TechDataTool()
        
        # 2. Thực thi tool với ticker được cung cấp
        # Chúng ta gọi trực tiếp hàm _run, giống như cách crewAI sẽ làm
        result = tech_tool._run(ticker=ticker)
        
        # 3. In kết quả
        print("\n--- KẾT QUẢ TRẢ VỀ TỪ TOOL ---\n")
        print(result)
        print("\n------------------------------")
        print(f">>> KIỂM TRA TechDataTool cho '{ticker}' THÀNH CÔNG!")
        
    except Exception as e:
        print(f"\n!!! ĐÃ XẢY RA LỖI NGHIÊM TRỌNG KHI CHẠY TechDataTool cho '{ticker}' !!!")
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()

def run_financial_tool_test(ticker):
    """Hàm để kiểm tra ComprehensiveFinancialTool."""
    print("\n" + "#"*50)
    print(f"BẮT ĐẦU KIỂM TRA: ComprehensiveFinancialTool với mã '{ticker}'")
    print("#"*50)
    
    try:
        # 1. Khởi tạo tool
        financial_tool = ComprehensiveFinancialTool()
        
        # 2. Thực thi tool
        result = financial_tool._run(ticker=ticker)
        
        # 3. In kết quả
        print("\n--- KẾT QUẢ TRẢ VỀ TỪ TOOL ---\n")
        print(result)
        print("\n------------------------------")
        print(f">>> KIỂM TRA ComprehensiveFinancialTool cho '{ticker}' THÀNH CÔNG!")

    except Exception as e:
        print(f"\n!!! ĐÃ XẢY RA LỖI NGHIÊM TRỌNG KHI CHẠY ComprehensiveFinancialTool cho '{ticker}' !!!")
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n*** Bắt đầu kịch bản kiểm tra độc lập cho các financial tools ***\n")

    # --- KỊCH BẢN 1: KIỂM TRA TECH TOOL VỚI CỔ PHIẾU ---
    run_tech_tool_test(ticker="HPG")
    
    # --- KỊCH BẢN 2: KIỂM TRA TECH TOOL VỚI CHỈ SỐ ---
    run_tech_tool_test(ticker="VNINDEX")

    # --- KỊCH BẢN 3: KIỂM TRA "SIÊU TOOL" TÀI CHÍNH VỚI CỔ PHIẾU ---
    run_financial_tool_test(ticker="HPG")
    
    print("\n*** Kịch bản kiểm tra đã hoàn tất ***")