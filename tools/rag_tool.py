# tools/rag_tool.py

from crewai.tools import BaseTool
from rag_engine import rag_engine

class GraphRAGTool(BaseTool):
    name: str = "Graph RAG Query Tool"
    description: str = "Dùng để hỏi các thông tin cụ thể từ tài liệu PDF đã được index. Input string format: 'TICKER|Câu hỏi'"

    def _run(self, query_input: str) -> str:
        try:
            if "|" in query_input:
                parts = query_input.split("|", 1)
                ticker = parts[0].strip()
                question = parts[1].strip()
            else:
                ticker = "VNINDEX" 
                question = query_input
            
            print(f"[RAG Tool] Querying for {ticker}: {question}")
            
            result = rag_engine.query_data(ticker, question)
            
            if not result:
                return "Không tìm thấy dữ liệu liên quan trong tài liệu PDF nội bộ."
            return str(result)
            
        except Exception as e:
            return f"Lỗi khi truy vấn RAG: {str(e)}"