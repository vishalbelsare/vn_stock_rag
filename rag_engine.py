import os
import logging
import sys
import shutil
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

logging.getLogger('llama_index').setLevel(logging.WARNING)

try:
    llm_key = key_manager.get_next_key()
    embed_key = key_manager.get_next_key()

    Settings.llm = Gemini(
        model="models/gemini-2.5-flash", 
        api_key=llm_key,
        temperature=0.1
    )
    
    Settings.embedding = GeminiEmbedding(
        model_name="models/text-embedding-004", 
        api_key=embed_key
    )
    
    Settings.chunk_size = 4096 
    Settings.chunk_overlap = 512
    
    print("✅ [RAG Engine] Đã cấu hình Gemini (Flash & Text-Embedding-004)")

except Exception as e:
    print(f"⚠️ [RAG Engine] Lỗi cấu hình API: {e}")

PERSIST_DIR = "./storage_rag"

QA_PROMPT_TMPL = (
    "Bạn là một trợ lý tài chính trung thực. Nhiệm vụ của bạn là trả lời câu hỏi CHỈ dựa trên thông tin được cung cấp dưới đây.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Câu hỏi: {query_str}\n"
    "\n"
    "QUY TẮC BẮT BUỘC:\n"
    "1. CHỈ sử dụng thông tin trong phần 'Context' ở trên. KHÔNG sử dụng kiến thức bên ngoài.\n"
    "2. Nếu thông tin không có trong Context, hãy trả lời chính xác cụm từ: 'NO_DATA_FOUND'.\n"
    "3. Trích dẫn nguyên văn con số và đơn vị nếu có.\n"
    "Câu trả lời:"
)
QA_TEMPLATE = PromptTemplate(QA_PROMPT_TMPL)

class FinancialRAG:
    def __init__(self):
        self.ocr_tool = MistralOCRTool()
        self._index_cache = {} 

    def _get_index_path(self, ticker):
        return os.path.join(PERSIST_DIR, ticker.upper().strip())

    def _load_index(self, ticker):
        ticker = ticker.upper().strip()
        if ticker in self._index_cache: return self._index_cache[ticker]

        persist_path = self._get_index_path(ticker)
        if not os.path.exists(persist_path): return None
        
        try:
            storage_context = StorageContext.from_defaults(persist_dir=persist_path)
            index = load_index_from_storage(
                storage_context,
                embed_model=Settings.embedding, # <--- ÉP DÙNG GEMINI
                llm=Settings.llm
            )
            self._index_cache[ticker] = index
            return index
        except Exception as e:
            print(f"❌ [RAG] Lỗi tải index {ticker}: {e}")
            return None

    def ingest_pdf(self, file_path, ticker):
        ticker = ticker.upper().strip()
        print(f"📥 [RAG] Đang xử lý file cho mã {ticker}...")
        
        # 1. OCR
        self.ocr_tool._run(file_path)
        base_name = os.path.splitext(file_path)[0]
        txt_path = f"{base_name}.ocr_text.txt"
        
        if not os.path.exists(txt_path): return None
        with open(txt_path, "r", encoding="utf-8") as f: text = f.read()
        if not text: return None

        doc = Document(text=text, metadata={"ticker": ticker})
        
        try:
            persist_path = self._get_index_path(ticker)
            
            if os.path.exists(persist_path):
                shutil.rmtree(persist_path)
                
            if not os.path.exists(persist_path): os.makedirs(persist_path)

            print(f"⚙️ [RAG] Đang Vector hóa dữ liệu (Gemini Embedding)...")
            
            index = VectorStoreIndex.from_documents(
                [doc],
                embed_model=Settings.embedding,
                llm=Settings.llm
            )
            
            index.storage_context.persist(persist_dir=persist_path)
            self._index_cache[ticker] = index
            
            print(f"✅ [RAG] Đã lưu xong dữ liệu {ticker}!")
            return index
        except Exception as e:
            print(f"❌ [RAG] Lỗi tạo index (Khả năng do hết quota hoặc sai key): {e}")
            return None

    def query_data(self, ticker, query_str, is_deep_analysis=False):
        index = self._load_index(ticker)
        if not index: return "NO_DATA: Chưa có dữ liệu."

        try:
            top_k = 30 if is_deep_analysis else 30
            
            query_engine = index.as_query_engine(
                similarity_top_k=top_k,
                text_qa_template=QA_TEMPLATE,
                response_mode="compact",
                llm=Settings.llm,
                embed_model=Settings.embedding 
            )
            
            response = query_engine.query(query_str)
            return str(response)

        except Exception as e:
            return f"Lỗi truy vấn RAG: {e}"

rag_engine = FinancialRAG()