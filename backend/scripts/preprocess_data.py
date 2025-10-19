import os
import sys


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from src.core import config
from src.services.chunking import VietnameseHistoryChunker
from src.services.embedding import EmbeddingPipeline

def main():
    """
    Hàm chính điều phối toàn bộ quá trình tiền xử lý dữ liệu:
    1. Kiểm tra file embedding đã tồn tại chưa.
    2. Nếu chưa, thực hiện chunking và embedding.
    3. Lưu kết quả ra file.
    """
    
    os.makedirs(config.PREPROCESSED_DATA_DIR, exist_ok=True)

    if os.path.exists(config.EMBEDDINGS_FILE_PATH):
        print(f"File embedding đã tồn tại tại '{config.EMBEDDINGS_FILE_PATH}'. Bỏ qua tiền xử lý.")
        return

    print("Bắt đầu quy trình tiền xử lý dữ liệu...")
    
    try:
        with open(config.MARKDOWN_FILE_PATH, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file tài liệu tại '{config.MARKDOWN_FILE_PATH}'")
        print("Vui lòng chạy data_pipeline trước để tạo file dữ liệu sạch.")
        return
        
    chunker = VietnameseHistoryChunker()
    chunks = chunker.chunk_markdown(markdown_content)
    chunker.save_chunks_to_json(chunks, config.CHUNKS_JSON_PATH)

    pipeline = EmbeddingPipeline(model_name=config.EMBEDDING_MODEL_NAME)
    embedded_chunks = pipeline.embed_chunks(chunks)

    pipeline.save_embeddings(embedded_chunks, config.EMBEDDINGS_FILE_PATH)
    
    print("\n hoàn thành quy trình tiền xử lý dữ liệu!")

if __name__ == "__main__":
    main()