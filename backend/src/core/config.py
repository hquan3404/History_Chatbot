import os
from dotenv import load_dotenv

# --- PATH CONFIGURATION ---
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOTENV_PATH = os.path.join(BACKEND_DIR, '.env')

# Tải các biến môi trường từ file .env
if os.path.exists(DOTENV_PATH):
    load_dotenv(dotenv_path=DOTENV_PATH)
else:
    print(f"Thông báo: Không tìm thấy file .env tại '{DOTENV_PATH}'. "
          "Đang tiếp tục với các biến môi trường hệ thống.")

DATA_PIPELINE_DIR = os.path.join(os.path.dirname(BACKEND_DIR), "data_pipeline")
MARKDOWN_FILE_PATH = os.path.join(DATA_PIPELINE_DIR, "data", "processed", "tai_lieu_hoan_chinh.md")

# Đường dẫn tới thư mục dữ liệu đã qua xử lý
PREPROCESSED_DATA_DIR = os.path.join(BACKEND_DIR, "data_processed")
CHUNKS_JSON_PATH = os.path.join(PREPROCESSED_DATA_DIR, "vietnam_history_chunks.json")
EMBEDDINGS_FILE_PATH = os.path.join(PREPROCESSED_DATA_DIR, "vietnam_history_embeddings.pkl")


# --- MODEL & API CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Tên các model
EMBEDDING_MODEL_NAME = 'keepitreal/vietnamese-sbert'
GENERATION_MODEL_NAME = 'gemini-2.5-flash' 

# --- RETRIEVER CONFIGURATION ---
SEMANTIC_WEIGHT = 0.5
KEYWORD_WEIGHT = 0.5

# --- VALIDATION ---
# Kiểm tra để đảm bảo API Key đã được thiết lập
if not GEMINI_API_KEY:
    raise ValueError("Lỗi: Biến môi trường 'GEMINI_API_KEY' chưa được thiết lập. "
                     "Vui lòng kiểm tra lại file .env của bạn.")