# History Chatbot — Hỏi đáp Lịch sử Việt Nam bằng RAG

Ứng dụng hỏi đáp và tạo câu hỏi trắc nghiệm từ tài liệu Lịch sử Việt Nam giai đoạn 1954–1975. Hệ thống dùng pipeline Retrieval-Augmented Generation (RAG): phân đoạn văn bản theo cấu trúc chương mục, tạo embedding tiếng Việt, tìm kiếm kết hợp ngữ nghĩa và từ khóa, rerank kết quả rồi đưa ngữ cảnh cho mô hình ngôn ngữ.

Backend cung cấp hai lựa chọn sinh câu trả lời: Qwen3 1.7B chạy cục bộ qua Ollama và Google Gemini. Giao diện React hỗ trợ chat có hiển thị nguồn tài liệu và tạo quiz theo chủ đề.

## Tính năng chính

- Hỏi đáp lịch sử dựa trên các đoạn tài liệu được truy xuất, kèm đường dẫn chương mục làm nguồn.
- Hybrid retrieval kết hợp semantic search với BM25.
- Reranking kết quả bằng các tín hiệu khớp câu hỏi, độ phủ từ khóa và ngày tháng.
- Sinh câu hỏi trắc nghiệm từ ngữ cảnh truy xuất được.
- Chạy Qwen3 1.7B cục bộ qua Ollama; Gemini là backend tùy chọn.
- Lưu lịch sử hội thoại trong trình duyệt.

## Pipeline RAG

~~~text
Câu hỏi
  → Vietnamese-SBERT tạo embedding truy vấn
  → Semantic search + BM25
  → Kết hợp điểm và lấy nhóm ứng viên
  → Heuristic reranking
  → Đưa các đoạn liên quan cùng metadata nguồn vào Qwen3 1.7B hoặc Gemini
  → Trả lời hoặc sinh quiz
~~~

Chunker đọc cấu trúc heading Markdown để giữ metadata phân cấp như giai đoạn, chương, mục và tiểu mục. Kích thước mục tiêu được cấu hình ở 512 token; mục dài được tách nhỏ hơn, còn các mục ngắn cùng cấp có thể được gộp. Một số nội dung đặc biệt như bảng hoặc niên biểu được giữ nguyên để tránh làm mất cấu trúc.

Embedding được tạo bằng Sentence-Transformers với model **keepitreal/vietnamese-sbert**. Retriever chuẩn hóa điểm semantic và BM25, kết hợp hai nguồn điểm với trọng số 0.5/0.5, sau đó rerank nhóm ứng viên trước khi chọn các đoạn cuối cùng. Reranker hiện là heuristic dựa trên khớp câu hỏi, độ phủ từ và ngày tháng; đây không phải cross-encoder reranker.

## Dữ liệu

Corpus chính là tài liệu Lịch sử Việt Nam

Quy trình dữ liệu trong workspace đi từ PDF và văn bản trích xuất/OCR đến Markdown đã làm sạch, sau đó tạo chunk và embedding. Metadata của chunk lưu nội dung cùng đường dẫn heading để hệ thống có thể trả lời kèm nguồn.

Index chunk hiện có trong **backend/data_processed/vietnam_history_chunks.json** gồm **1.704 chunk**: 827 chunk cho giai đoạn 1954–1965 và 877 chunk cho giai đoạn 1965–1975. Embedding tương ứng được lưu trong **backend/data_processed/vietnam_history_embeddings.pkl**.

Các bộ CSV đánh giá và dữ liệu nằm dưới **data_pipeline/data/**. Trong workspace hiện tại, các tệp đánh giá có số dòng:

| Tệp | Số bản ghi | Nội dung |
|---|---:|---|
| qa_pairs.csv | 100 | Hỏi đáp lịch sử tổng quát |
| yen_tu_qa.csv | 538 | Hỏi đáp về Yên Tử |
| finetune_data.csv | 502 | Bản ghi hỏi đáp bổ trợ |

Thư mục **data_pipeline/data/** được loại khỏi Git bằng **.gitignore**, nên PDF, Markdown nguồn và các CSV này không có trong một bản clone sạch. Index chunk và embedding đã tạo sẵn có trong **backend/data_processed/**. Nếu muốn tạo lại index, cần đặt Markdown đã làm sạch vào **data_pipeline/data/processed/1954-1965/** và **data_pipeline/data/processed/1965-1975/**.

## Kết quả benchmark

Bảng dưới đây ghi lại các số liệu được cung cấp trong CV. Các chỉ số nằm trong khoảng 0–1; giá trị cao hơn là tốt hơn.

### Retrieval

| Chỉ số | Baseline | Hybrid retrieval + reranking | Mức thay đổi |
|---|---:|---:|---:|
| Hit@5 | 0.632 | **0.881** | **+0.249** |
| MRR | 0.664 | **0.818** | **+0.154** |

Hit@5 đo tỷ lệ câu hỏi có ít nhất một đoạn liên quan trong top 5 kết quả. MRR là trung bình nghịch đảo thứ hạng của kết quả liên quan đầu tiên; chỉ số này thưởng cho việc tìm thấy đoạn đúng ở vị trí cao hơn.

### Chất lượng câu trả lời

So sánh Qwen 1.7B baseline với Qwen 1.7B được bổ sung pipeline RAG:

| Chỉ số | Qwen 1.7B baseline | Qwen 1.7B + RAG | Mức thay đổi |
|---|---:|---:|---:|
| Faithfulness | 0.591 | **0.832** | **+0.241** |
| Answer relevancy | 0.623 | **0.768** | **+0.145** |
| Answer correctness | 0.396 | **0.712** | **+0.316** |

Faithfulness phản ánh mức độ câu trả lời được hỗ trợ bởi ngữ cảnh truy xuất. Answer relevancy đo mức độ câu trả lời bám sát câu hỏi. Answer correctness đo độ đúng so với đáp án chuẩn.

## Cài đặt và chạy

### Yêu cầu

- Python 3.10 trở lên
- Node.js và npm
- Ollama nếu chạy Qwen cục bộ
- Các file embedding có sẵn trong **backend/data_processed/**, hoặc corpus Markdown nếu cần tạo lại index

### 1. Cài backend

Từ thư mục gốc của repo:

~~~bash
pip install -r requirements.txt
~~~

Nếu dùng Gemini, tạo file cấu hình từ mẫu và điền API key:

~~~bash
cp backend/.env.example backend/.env
~~~

Qwen chạy qua Ollama. Cài Ollama, khởi động dịch vụ rồi tải model:

~~~bash
ollama pull qwen3:1.7b
~~~

Nếu cần tạo lại chunks và embeddings sau khi đã đặt các file Markdown nguồn đúng thư mục:

~~~bash
python backend/scripts/preprocess_data.py
~~~

Lệnh này tạo **vietnam_history_chunks.json** và **vietnam_history_embeddings.pkl** trong **backend/data_processed/**.

### 2. Khởi động backend

~~~bash
cd backend
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
~~~

API chat dùng **/api/v1/chat**; API tạo quiz dùng **/api/v1/generate_quiz**.

### 3. Khởi động frontend

Mở terminal khác:

~~~bash
cd frontend
npm install
npm run dev
~~~

Mở địa chỉ http://localhost:3000. Trong giao diện, chọn Qwen để gửi yêu cầu tới Ollama hoặc chọn Gemini nếu đã cấu hình API key.

## Cấu trúc repo

~~~text
backend/
  scripts/preprocess_data.py
  src/
    core/config.py
    main.py
    services/
      chunking.py
      embedding.py
      retrieval.py
      generation.py
  data_processed/
    vietnam_history_chunks.json
    vietnam_history_embeddings.pkl

data_pipeline/
  data/                         # Dữ liệu cục bộ, bị loại khỏi Git
  *.ipynb                       # Notebook thu thập và xử lý dữ liệu

evaluation/
  llm_judge_eval.py
  plot_metrics.py
  results/

frontend/
  App.tsx
  components/
  services/
  styles.css
~~~

## Công nghệ

| Thành phần | Công nghệ |
|---|---|
| Backend API | Python, FastAPI, Uvicorn |
| Frontend | React, TypeScript, Vite |
| Embedding | Sentence-Transformers, Vietnamese-SBERT |
| Retrieval | Cosine similarity, BM25, heuristic reranking |
| Sinh câu trả lời | Qwen3 1.7B qua Ollama, Google Gemini tùy chọn |
| Dữ liệu | Tài liệu Lịch sử Việt Nam 1954–1975 |
