# from fastapi import FastAPI
# from pydantic import BaseModel
# import os

# # Import các thành phần từ app
# from .core import config
# from .services.embedding import EmbeddingPipeline
# from .services.retrieval import HybridRetriever

# # --- KHỞI TẠO CÁC ĐỐI TƯỢNG KHI SERVER BẮT ĐẦU ---

# # Kiểm tra xem file embedding có tồn tại không
# if not os.path.exists(config.EMBEDDINGS_FILE_PATH):
#     print("="*80)
#     print(f"LỖI: File embedding '{config.EMBEDDINGS_FILE_PATH}' không tồn tại.")
#     print("Vui lòng chạy script tiền xử lý trước khi khởi động server:")
#     print("python scripts/preprocess_data.py")
#     print("="*80)
#     exit()

# # Tải các model và dữ liệu (chỉ một lần)
# print("--- Khởi tạo Server ---")
# print("1. Tải embedding pipeline...")
# pipeline = EmbeddingPipeline(model_name=config.EMBEDDING_MODEL_NAME)

# print(f"2. Tải dữ liệu chunks đã được embed từ '{config.EMBEDDINGS_FILE_PATH}'...")
# embedded_chunks = pipeline.load_embeddings(config.EMBEDDINGS_FILE_PATH)

# print("3. Khởi tạo retriever...")
# retriever = HybridRetriever(
#     embedded_chunks=embedded_chunks,
#     embedding_pipeline=pipeline,
#     semantic_weight=config.SEMANTIC_WEIGHT,
#     keyword_weight=config.KEYWORD_WEIGHT
# )
# print("✅ Server đã sẵn sàng nhận yêu cầu!")
# print("-" * 25)

# # Khởi tạo FastAPI app
# app = FastAPI(title="Lich Su Vietnam RAG API")

# # --- ĐỊNH NGHĨA API ENDPOINTS ---

# class QueryRequest(BaseModel):
#     query: str
#     top_k: int = 5

# @app.get("/")
# def read_root():
#     return {"message": "Welcome to the Vietnamese History RAG API!"}

# @app.post("/api/v1/chat")
# def chat_with_history(request: QueryRequest):
#     """
#     Nhận câu hỏi từ người dùng và trả về các chunk liên quan nhất.
#     """
#     print(f"Received query: '{request.query}' with top_k={request.top_k}")
    
#     results = retriever.retrieve_with_rerank(
#         query=request.query, 
#         top_k=request.top_k,
#         candidate_k=20 # candidate_k có thể được cấu hình nếu muốn
#     )
    
#     return {"query": request.query, "results": results}


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from fastapi.middleware.cors import CORSMiddleware
from .core import config
from .services.embedding import EmbeddingPipeline
from .services.retrieval import HybridRetriever
from .services.generation import GeminiRAGGenerator

# Kiểm tra xem file embedding
if not os.path.exists(config.EMBEDDINGS_FILE_PATH):
    print("="*80)
    print(f"LỖI: File embedding '{config.EMBEDDINGS_FILE_PATH}' không tồn tại.")
    print("Vui lòng chạy script tiền xử lý trước khi khởi động server:")
    print("python scripts/preprocess_data.py")
    print("="*80)
    exit()

# --- KHỞI TẠO CÁC ĐỐI TƯỢNG SINGLETON KHI SERVER BẮT ĐẦU ---
print("--- Khởi tạo Server ---")

print("1. Tải embedding pipeline...")
embedding_pipeline = EmbeddingPipeline(model_name=config.EMBEDDING_MODEL_NAME)

print(f"2. Tải dữ liệu chunks đã được embed từ '{config.EMBEDDINGS_FILE_PATH}'...")
embedded_chunks = embedding_pipeline.load_embeddings(config.EMBEDDINGS_FILE_PATH)

print("3. Khởi tạo retriever...")
retriever = HybridRetriever(
    embedded_chunks=embedded_chunks,
    embedding_pipeline=embedding_pipeline,
    semantic_weight=config.SEMANTIC_WEIGHT,
    keyword_weight=config.KEYWORD_WEIGHT
)

print("4. Khởi tạo Gemini RAG Generator...")
generator = GeminiRAGGenerator()

print("Server đã sẵn sàng nhận yêu cầu!")
print("-" * 25)

# Khởi tạo FastAPI app
app = FastAPI(title="Lich Su Vietnam RAG API")
origins = ["*"] # Cho phép tất cả các nguồn
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Cho phép tất cả các phương thức (GET, POST, etc.)
    allow_headers=["*"], # Cho phép tất cả các header
)
# --- ĐỊNH NGHĨA API ENDPOINTS ---

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5 # Số lượng context chunk muốn truy xuất

@app.get("/")
def read_root():
    return {"message": "Welcome to the Vietnamese History RAG API!"}

@app.post("/api/v1/chat")
def chat_with_history(request: QueryRequest):
    """
    Endpoint chính để thực hiện RAG: nhận câu hỏi, truy xuất ngữ cảnh và sinh câu trả lời.
    """
    print(f"Received query: '{request.query}' with top_k={request.top_k}")

    if not generator.model:
        raise HTTPException(
            status_code=500, 
            detail="Dịch vụ sinh câu trả lời không khả dụng. Vui lòng kiểm tra cấu hình server."
        )
    
    # RETRIEVAL - Lấy các chunk ngữ cảnh liên quan
    print(f"Đang truy xuất {request.top_k} chunk liên quan...")
    retrieved_chunks = retriever.retrieve_with_rerank(
        query=request.query, 
        top_k=request.top_k,
        candidate_k=20 # Lấy 20 ứng viên ban đầu để rerank
    )
    
    if not retrieved_chunks:
        return {
            "query": request.query,
            "response": {
                "answer": "Rất tiếc, tôi không tìm thấy bất kỳ tài liệu nào liên quan đến câu hỏi của bạn.",
                "sources": []
            }
        }

    # GENERATION - Dùng context và query để sinh câu trả lời
    print("Đang sinh câu trả lời từ các chunk đã truy xuất...")
    final_response = generator.generate_answer(
        query=request.query,
        context_chunks=retrieved_chunks
    )
    
    return {"query": request.query, "response": final_response}
