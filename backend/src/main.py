from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional

from .core import config
from .services.embedding import EmbeddingPipeline
from .services.retrieval import HybridRetriever
from .services.generation import (
    BaseRAGGenerator, 
    GeminiRAGGenerator, 
    QwenOllamaGenerator,
    log_retrieved_chunks 
)

print("load embedding...")
embedding_pipeline = EmbeddingPipeline(model_name=config.EMBEDDING_MODEL_NAME)
print(f"load data embedding... '{config.EMBEDDINGS_FILE_PATH}'...")
embedded_chunks = embedding_pipeline.load_embeddings(config.EMBEDDINGS_FILE_PATH)
print("create retriever...")
retriever = HybridRetriever(
    embedded_chunks=embedded_chunks,
    embedding_pipeline=embedding_pipeline,
    semantic_weight=config.SEMANTIC_WEIGHT,
    keyword_weight=config.KEYWORD_WEIGHT
)
print("create generators...")
generators: Dict[str, BaseRAGGenerator] = {
    "gemini": GeminiRAGGenerator(),
    "qwen": QwenOllamaGenerator()
}
print("Gemini Generator Loaded.")
print("Qwen Generator Loaded.")

# Khởi tạo FastAPI app
app = FastAPI(title="Lich Su Vietnam RAG API")

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#API ENDPOINTS

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5 
    model: str = "gemini"

# Pydantic model cho Quiz Request
class QuizRequest(BaseModel):
    topic: Optional[str] = None 
    k: int = 3 # k câu hỏi
    model: str = "gemini"

@app.get("/")
def read_root():
    return {"message": "Welcome to the Vietnamese History RAG API!"}

@app.post("/api/v1/chat")
def chat_with_history(request: QueryRequest):
    print(f"Received query: '{request.query}' with top_k={request.top_k}, model='{request.model}'")
    generator_to_use = generators.get(request.model)
    if not generator_to_use:
        raise HTTPException(
            status_code=400, 
            detail=f"Model '{request.model}' không hợp lệ. Chỉ chấp nhận 'gemini' hoặc 'qwen'."
        )
    
    if not generator_to_use.is_ready():
        raise HTTPException(
            status_code=500,
            detail=f"hệ thống sinh câu trả lời cho model '{request.model}' không khả dụng. Kiểm tra log server."
        )
    
    print(f"Đang truy xuất {request.top_k} chunk liên quan...")
    retrieved_chunks = retriever.retrieve_with_rerank(
        query=request.query, 
        top_k=request.top_k,
        candidate_k=20 
    )
    
    if not retrieved_chunks:
        return {
            "query": request.query,
            "response": {
                "answer": "Rất tiếc, tôi không tìm thấy bất kỳ tài liệu nào liên quan đến câu hỏi của bạn.",
                "sources": []
            }
        }

    log_retrieved_chunks(request.query, retrieved_chunks)

    print(f"Đang sinh câu trả lời (sử dụng model {request.model})...")
    
    final_response = generator_to_use.generate_answer(
        query=request.query,
        context_chunks=retrieved_chunks
    )
    
    return {"query": request.query, "response": final_response}

# endpoint sinh câu hỏi trắc nghiệm
@app.post("/api/v1/generate_quiz")
def generate_quiz(request: QuizRequest):
    print(f"Received quiz request: k={request.k}, topic='{request.topic}', model='{request.model}'")
    # Chọn Generator
    generator_to_use = generators.get(request.model)

    if not generator_to_use:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{request.model}' không hợp lệ. Chỉ chấp nhận 'gemini' hoặc 'qwen'."
        )
    
    if not generator_to_use.is_ready():
        raise HTTPException(
            status_code=500,
            detail=f"Dịch vụ sinh câu trả lời cho model '{request.model}' không khả dụng."
        )

    # Lấy Ngữ cảnh
    # Nếu không có topic, dùng 1 query chung để lấy chunk ngẫu nhiên
    if not request.topic or request.topic.strip() == "":
        query_for_retrieval = "Các sự kiện lịch sử Việt Nam 1954-1975"
        print("Không có chủ đề, dùng query ngẫu nhiên...")
    else:
        query_for_retrieval = request.topic
    
    # Lấy 5 chunk để làm ngữ cảnh
    print(f"Đang truy xuất 5 chunk cho chủ đề: '{query_for_retrieval}'...")
    retrieved_chunks = retriever.retrieve_with_rerank(
        query=query_for_retrieval, 
        top_k=5, 
        candidate_k=20
    )
    
    if not retrieved_chunks:
        return {
            "status": "error",
            "message": "Rất tiếc, tôi không tìm thấy bất kỳ tài liệu nào liên quan đến chủ đề này."
        }
    
    log_retrieved_chunks(query_for_retrieval, retrieved_chunks)

    # Sinh Câu hỏi
    print(f"Đang sinh {request.k} câu hỏi trắc nghiệm (sử dụng model {request.model})...")
    
    quiz_response = generator_to_use.generate_quiz(
        context_chunks=retrieved_chunks,
        k=request.k
    )
    
    # quiz_response có dạng {"status": "...", "questions": ...} hoặc {"status": "error", "message": ...}
    return quiz_response

