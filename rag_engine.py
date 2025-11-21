import os
import logging
import threading
from llama_index.core import (
    VectorStoreIndex,
    Document, 
    StorageContext, 
    load_index_from_storage, 
    Settings,
    PromptTemplate
)
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from key_manager import key_manager
from tools.ocr_tool import MistralOCRTool

logging.getLogger('llama_index').setLevel(logging.ERROR)

try:
    llm_key = key_manager.get_next_key()
    embed_key = key_manager.get_next_key()

    Settings.llm = Gemini(
        model_name="models/gemini-2.5-flash", 
        api_key=llm_key,
        temperature=0.1 
    )
    
    Settings.embedding = GeminiEmbedding(
        model_name="models/text-embedding-004", 
        api_key=embed_key
    )
    
    Settings.chunk_size = 2048 
    Settings.chunk_overlap = 50 

except Exception as e:
    print(f"⚠️ Lỗi cấu hình LlamaIndex: {e}")

PERSIST_DIR = "./storage_rag"

FAST_QA_TEMPLATE = PromptTemplate(
    "Dữ liệu tham khảo:\n{context_str}\n"
    "Câu hỏi: {query_str}\n"
    "Yêu cầu: Trả lời cực ngắn gọn dựa trên dữ liệu. Nếu không có số liệu, ghi 'NO_DATA'."
)

_index_cache = {}
_lock = threading.Lock()

class FinancialRAG:
    def __init__(self):
        self.ocr_tool = MistralOCRTool()
        
    def _get_index(self, ticker):
        """
        Hàm cốt lõi để lấy Index siêu tốc.
        Ưu tiên lấy từ RAM -> Nếu không có mới load từ Disk -> Lưu vào RAM.
        """
        ticker = ticker.upper().strip() 

        if ticker in _index_cache:
            return _index_cache[ticker]

        with _lock:
            if ticker in _index_cache:
                return _index_cache[ticker]

            ticker_persist_dir = os.path.join(PERSIST_DIR, ticker)
            if not os.path.exists(ticker_persist_dir):
                return None
            
            try:
                storage_context = StorageContext.from_defaults(persist_dir=ticker_persist_dir)
                index = load_index_from_storage(
                    storage_context,
                    embed_model=Settings.embedding,
                    llm=Settings.llm
                )
                _index_cache[ticker] = index
                return index
            except Exception as e:
                print(f"❌ Lỗi load index {ticker}: {e}")
                return None

    def ingest_pdf(self, file_path, ticker):
        """Xử lý file PDF mới"""
        print(f"[RAG] Đang số hóa tài liệu: {os.path.basename(file_path)}...")
        
        self.ocr_tool._run(file_path)
        base_name = os.path.splitext(file_path)[0]
        txt_path = f"{base_name}.ocr_text.txt"
        
        if not os.path.exists(txt_path): return None

        with open(txt_path, "r", encoding="utf-8") as f:
            text_content = f.read()

        if not text_content: return None

        new_doc = Document(text=text_content, metadata={"ticker": ticker})
        
        with _lock:
            if ticker in _index_cache:
                del _index_cache[ticker]

        try:
            index = VectorStoreIndex.from_documents(
                [new_doc],
                embed_model=Settings.embedding,
                llm=Settings.llm
            )
            
            ticker_persist_dir = os.path.join(PERSIST_DIR, ticker)
            if not os.path.exists(ticker_persist_dir): os.makedirs(ticker_persist_dir)
            index.storage_context.persist(persist_dir=ticker_persist_dir)
            
            with _lock:
                _index_cache[ticker] = index
                
            print(f"✅ [RAG] Đã nạp xong dữ liệu {ticker}!")
            return index
        except Exception as e:
            print(f"❌ Lỗi ingest: {e}")
            return None

    def query_data(self, ticker, query_str, is_deep_analysis=False):
        """
        Truy vấn dữ liệu.
        Args:
            is_deep_analysis (bool): 
                - False (Mặc định): Chế độ Chat nhanh. Chỉ lấy 10 docs. Phản hồi < 2s.
                - True: Chế độ Phân tích sâu. Lấy 20 docs. Phản hồi chi tiết.
        """
        ticker = str(ticker).upper().strip()
        
        index = self._get_index(ticker)
        if not index: return None

        try:
            if is_deep_analysis:
                top_k = 20
                qa_template = None 
            else:
                top_k = 10 
                qa_template = FAST_QA_TEMPLATE 

            query_engine = index.as_query_engine(
                similarity_top_k=top_k,
                response_mode="compact", 
                text_qa_template=qa_template,
                llm=Settings.llm,
                streaming=False 
            )
            
            response = query_engine.query(query_str)
            return str(response)

        except Exception as e:
            return f"Lỗi truy vấn RAG: {e}"

rag_engine = FinancialRAG()