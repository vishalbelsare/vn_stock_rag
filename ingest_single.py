from dotenv import load_dotenv
load_dotenv()

import os
import sys
import time
import logging

try:
    from llama_index.core import VectorStoreIndex, Document, Settings
    from llama_index.embeddings.gemini import GeminiEmbedding
    from llama_index.llms.gemini import Gemini
    from key_manager import key_manager
    from tools.ocr_tool import MistralOCRTool
except ImportError as e:
    print(f"❌ Thiếu thư viện: {e}")
    sys.exit(1)

# Cấu hình Log
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"
logging.getLogger('llama_index').setLevel(logging.WARNING)

PERSIST_DIR = "./storage_rag"

def get_ticker_from_filename(filename):
    try:
        base_name = os.path.basename(filename).split('.')[0]
        ticker = base_name.split('-')[0].strip().upper()
        if 3 <= len(ticker) <= 5:
            return ticker
        return None
    except:
        return None

def ingest_single_file(file_path):
    if not os.path.exists(file_path):
        print(f"❌ File không tồn tại: {file_path}")
        return

    filename = os.path.basename(file_path)
    print(f"🚀 Bắt đầu xử lý file: {filename}")

    ticker = get_ticker_from_filename(filename)
    if not ticker:
        print("⚠️ Không tự động nhận diện được Ticker từ tên file.")
        ticker = input("👉 Vui lòng nhập mã cổ phiếu (VD: FPT): ").strip().upper()
    
    print(f"📌 Mã cổ phiếu: {ticker}")

    # 2. Cấu hình Gemini
    try:
        api_key = key_manager.get_next_key()
        embed_model = GeminiEmbedding(model_name="models/text-embedding-004", api_key=api_key)
        llm = Gemini(model_name="models/gemini-2.5-pro", api_key=api_key)
        
        Settings.llm = llm
        Settings.embed_model = embed_model
        Settings.chunk_size = 4096
        Settings.chunk_overlap = 512
    except Exception as e:
        print(f"❌ Lỗi cấu hình API Key: {e}")
        return

    # 3. OCR (Chuyển PDF -> Text)
    ocr_tool = MistralOCRTool()
    
    # Kiểm tra xem file text đã có sẵn chưa (Do bạn nói đã OCR rồi)
    base_path = os.path.splitext(file_path)[0]
    txt_path = f"{base_path}.ocr_text.txt"
    text_content = ""

    if os.path.exists(txt_path):
        print(f"ℹ️ Tìm thấy file OCR text có sẵn: {os.path.basename(txt_path)}")
        with open(txt_path, "r", encoding="utf-8") as f:
            text_content = f.read()
    else:
        print(f"📖 Đang chạy OCR (Mistral) cho file PDF...")
        try:
            ocr_tool._run(file_path)
            # Sau khi run, tool tự tạo file .ocr_text.txt
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    text_content = f.read()
            else:
                print("❌ Lỗi: Không tìm thấy file text sau khi chạy OCR tool.")
                return
        except Exception as e:
            print(f"❌ Lỗi OCR: {e}")
            return

    if not text_content:
        print("❌ Nội dung văn bản rỗng.")
        return

    # 4. Embedding & Indexing
    print(f"⚙️ Đang tạo Vector Index (Gemini Embedding)...")
    try:
        doc = Document(text=text_content, metadata={"ticker": ticker, "source": filename})
        index = VectorStoreIndex.from_documents(
            [doc],
            embed_model=embed_model,
            llm=llm
        )

        # Lưu vào thư mục storage_rag/TICKER
        save_dir = os.path.join(PERSIST_DIR, ticker)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        
        index.storage_context.persist(persist_dir=save_dir)
        print(f"✅ THÀNH CÔNG! Dữ liệu đã được lưu tại: {save_dir}")
        print(f"👉 Bây giờ bạn có thể chat hỏi về mã {ticker}.")

    except Exception as e:
        print(f"❌ Lỗi trong quá trình Vector hóa: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    else:
        print("ℹ️ Chưa nhập đường dẫn file.")
        target_file = "financial_reports/VNM-Q3.pdf"
    
    ingest_single_file(target_file)