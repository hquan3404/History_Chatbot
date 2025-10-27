import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from typing import List, Dict, Set
import requests
import os
import json

from src.core.config import (
    GEMINI_API_KEY, 
    GENERATION_MODEL_NAME,
    OLLAMA_API_URL,
    OLLAMA_MODEL_NAME 
)

# in log
def log_retrieved_chunks(query: str, context_chunks: List[Dict]):
    print("\n" + "="*80)
    print(f"Đã truy vấn được {len(context_chunks)} chunks cho câu hỏi: '{query}'")
    
    unique_sources_paths: Set[str] = set()
    for i, chunk in enumerate(context_chunks):
        source_path = chunk.get("metadata", {}).get("hierarchy_path", "N/A")
        unique_sources_paths.add(source_path)
        
        final_score = chunk.get("final_score", 0.0)
        rerank_score = chunk.get("rerank_score", 0.0)
        combined_score = chunk.get("combined_score", 0.0)
        semantic_score = chunk.get("semantic_score", 0.0)
        keyword_score = chunk.get("keyword_score", 0.0)

        print(f"\n--- Chunk {i+1} (Rank: {chunk.get('rank', 'N/A')}) ---")
        print(f" 	- Nguồn 	 	 	: {source_path}")
        print(f" 	- Điểm số cuối cùng: {final_score:.4f}")
        print(f" 	 	 	├─ Rerank 	: {rerank_score:.4f}")
        print(f" 	 	 	├─ Combined 	: {combined_score:.4f}")
        print(f" 	 	 	│ 	 ├─ Semantic: {semantic_score:.4f} (vector search)")
        print(f" 	 	 	│ 	 └─ Keyword : {keyword_score:.4f} (BM25)")
        print(f" 	- Nội dung 	 	 	: \"{chunk.get('content', '')[:250]}...\"")
    
    print("\n" + "="*80)
    print("Nguồn chính được sử dụng để tổng hợp câu trả lời:")
    if unique_sources_paths:
        for source in sorted(list(unique_sources_paths)):
            print(f" 	- {source}")
    else:
        print(" 	Không có nguồn cụ thể nào được tìm thấy.")
    print("="*80)


class BaseRAGGenerator:
    def _create_prompt(self, query: str, context_chunks: List[Dict]) -> str:
        context_texts = [chunk['content'] for chunk in context_chunks]
        context = "\n\n---\n\n".join(context_texts)

        prompt_template = f"""
        Bạn là một trợ lý AI chuyên gia về Lịch sử Việt Nam giai đoạn kháng chiến chống Mỹ (1954-1975).
        Nhiệm vụ của bạn là trả lời câu hỏi của người dùng chỉ dựa vào bối cảnh được cung cấp.

        BỐI CẢNH:
        ---
        {context}
        ---

        Dựa vào **CHỈ** bối cảnh trên, hãy trả lời câu hỏi sau đây một cách chi tiết, chính xác và mạch lạc.
        - Nếu thông tin không có trong bối cảnh, hãy trả lời rằng: "Tôi không tìm thấy thông tin về vấn đề này trong tài liệu được cung cấp."
        - Tuyệt đối không suy diễn hay bịa đặt thông tin.
        - Trình bày câu trả lời rõ ràng, có thể dùng gạch đầu dòng nếu cần.

        CÂU HỎI: {query}

        CÂU TRẢ LỜI:
        """
        return prompt_template.strip()
    
# prompt cho quizz
    def _create_quiz_prompt(self, context_chunks: List[Dict], k: int) -> str:
        """
        Tạo một prompt yêu cầu LLM sinh câu hỏi trắc nghiệm dưới dạng JSON.
        """
        context_texts = [chunk['content'] for chunk in context_chunks]
        context = "\n\n---\n\n".join(context_texts)

        # Định nghĩa cấu trúc JSON mong muốn
        json_schema = """
        [
            {
                "question": "Nội dung câu hỏi trắc nghiệm bằng tiếng Việt",
                "options": {
                    "A": "Nội dung đáp án A",
                    "B": "Nội dung đáp án B",
                    "C": "Nội dung đáp án C",
                    "D": "Nội dung đáp án D"
                },
                "correct_answer": "A"
            },
            ...
        ]
        """

        prompt_template = f"""
        Bạn là một chuyên gia tạo câu hỏi trắc nghiệm Lịch sử Việt Nam.
        Nhiệm vụ của bạn là tạo ra chính xác {k} câu hỏi trắc nghiệm chỉ dựa vào bối cảnh được cung cấp.

        BỐI CẢNH:
        ---
        {context}
        ---

        YÊU CẦU BẮT BUỘC:
        1. Tạo chính xác {k} câu hỏi trắc nghiệm.
        2. Mỗi câu hỏi phải có 4 lựa chọn (A, B, C, D) và MỘT đáp án đúng.
        3. Tất cả câu hỏi và đáp án phải bằng tiếng Việt.
        4. Trả lời CHỈ bằng một MẢNG (LIST) JSON hợp lệ theo cấu trúc sau:
        {json_schema}
        
        5. KHÔNG được thêm bất kỳ văn bản, lời giải thích, hay markdown (ví dụ: ```json ... ```) nào khác vào câu trả lời. Chỉ trả về MẢNG JSON.

        MẢNG JSON GỒM {k} CÂU HỎI:
        """
        return prompt_template.strip()


    def _format_sources(self, context_chunks: List[Dict]) -> List[Dict]:
        return [
            {
                "id": chunk["chunk_id"],
                "hierarchy": chunk.get("metadata", {}).get("hierarchy_path", "N/A"),
                "content_preview": chunk.get("content", "")[:150] + "..."
            }
            for chunk in context_chunks
        ]

    def generate_answer(self, query: str, context_chunks: List[Dict]) -> Dict:
        raise NotImplementedError("Subclass phải cài đè hàm generate_answer")
    def is_ready(self) -> bool:
        raise NotImplementedError("Subclass phải cài đè hàm is_ready")
    def generate_quiz(self, context_chunks: List[Dict], k: int) -> Dict:
        raise NotImplementedError("Subclass phải cài đè hàm generate_quiz")
    def is_ready(self) -> bool:
        raise NotImplementedError("Subclass phải cài đè hàm is_ready")
    
# gemini API
class GeminiRAGGenerator(BaseRAGGenerator):
    def __init__(self):
        super().__init__()
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            self.model = genai.GenerativeModel(
                model_name=GENERATION_MODEL_NAME,
                safety_settings=self.safety_settings
            )
            
            self.generation_config = {
                "temperature": 0.1,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 8192,
            }
            print("Khởi tạo Gemini model thành công!")

        except Exception as e:
            print(f"lỗi khởi tạo Gemini: {e}")
            self.model = None

    def is_ready(self) -> bool:
        return self.model is not None

    def generate_answer(self, query: str, context_chunks: List[Dict]) -> Dict: # <<< THAY ĐỔI
        if not self.is_ready():
            return {"answer": "Lỗi: Model Gemini chưa được khởi tạo.", "sources": []}
        prompt = super()._create_prompt(query, context_chunks)
        sources_for_frontend = super()._format_sources(context_chunks)
        
        print("\nGửi yêu cầu đến Gemini API và chờ câu trả lời...")
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            if response.parts:
                answer = "".join(part.text for part in response.parts)
                print("Gemini đã trả về câu trả lời.")
                if response.candidates[0].finish_reason.name == "MAX_TOKSENS":
                    answer += "\n\n...(Phản hồi có thể đã bị cắt ngắn do đạt đến giới hạn độ dài tối đa)..."
            else:
                finish_reason = response.candidates[0].finish_reason.name
                print(f"Gemini không trả về nội dung. Lý do: {finish_reason}")
                answer = f"Rất tiếc, không thể tạo câu trả lời. Lý do từ API: {finish_reason}"

        except Exception as e:
            print(f"Lỗi khi gọi Gemini API: {e}")
            answer = f"Đã xảy ra lỗi khi gọi Gemini API: {e}"

        return {"answer": answer, "sources": sources_for_frontend}
    
    def generate_quiz(self, context_chunks: List[Dict], k: int) -> Dict:
        if not self.is_ready():
            return {"status": "error", "message": "Lỗi: Model Gemini chưa được khởi tạo."}

        prompt = super()._create_quiz_prompt(context_chunks, k)
        
        quiz_generation_config = {
            "temperature": 0.2, 
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }
        
        print(f"\nGửi yêu cầu (quiz) đến Gemini API (yêu cầu JSON)...")
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=quiz_generation_config
            )
            
            if not response.parts:
                finish_reason = response.candidates[0].finish_reason.name
                print(f"Gemini không trả về nội dung. Lý do: {finish_reason}")
                return {"status": "error", "message": f"Rất tiếc, không thể tạo câu hỏi. Lý do từ API: {finish_reason}"}

            json_text = "".join(part.text for part in response.parts)
        
            questions_list = json.loads(json_text)
            print(f"Gemini đã trả về {len(questions_list)} câu hỏi trắc nghiệm (dạng JSON).")
            
            return {"status": "success", "questions": questions_list}

        except json.JSONDecodeError as e:
            print(f"Gemini không trả về JSON hợp lệ. Lỗi: {e}")
            print(f"Nội dung trả về: {json_text[:500]}...")
            return {"status": "error", "message": "Lỗi: Model trả về dữ liệu không đúng định dạng JSON."}
        except Exception as e:
            print(f"Lỗi khi gọi Gemini API (quiz): {e}")
            return {"status": "error", "message": f"Đã xảy ra lỗi khi gọi Gemini API: {e}"}

# Qwen Ollama
class QwenOllamaGenerator(BaseRAGGenerator):
    def __init__(self):
        super().__init__()
        self.api_url = f"{OLLAMA_API_URL}/api/generate" # gọi api ollama
        self.model_name = OLLAMA_MODEL_NAME
        self.session = requests.Session()
        self._ready = False
        
        print(f"Khởi tạo Qwen (Ollama) Generator, trỏ tới: {self.api_url}")
        print(f"Model: {self.model_name}")
        
        # Kiểm tra kết nối ngay khi khởi tạo
        if self.check_connection():
            self._ready = True
            print("đã kết nối tới Ollama")
        else:
            print(f"Không thể kết nối đến Ollama tại {OLLAMA_API_URL}")

    def check_connection(self) -> bool:
        try:
            response = self.session.get(OLLAMA_API_URL, timeout=3)
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Lỗi kết nối Ollama: {e}")
            return False

    def is_ready(self) -> bool:
        return self._ready

    def generate_answer(self, query: str, context_chunks: List[Dict]) -> Dict:
        if not self.is_ready():
            return {"answer": "Lỗi: Model Qwen (Ollama) chưa sẵn sàng.", "sources": []}
        prompt = super()._create_prompt(query, context_chunks)
        sources_for_frontend = super()._format_sources(context_chunks)

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": { 
                "temperature": 0.1,
                "top_p": 1,
                "top_k": 1,
                "num_ctx": 4096
            }
        }
        
        print(f"\nGửi yêu cầu đến Ollama ({self.model_name})...")
        try:
            response = self.session.post(self.api_url, json=payload, timeout=120) 
            response.raise_for_status()
            
            response_json = response.json()
            answer = response_json.get("response")
            
            if not answer:
                answer = "Lỗi: Ollama trả về JSON nhưng không có 'response'."
            
            print("Ollama đã trả về câu trả lời.")

        except requests.Timeout:
            print("Yêu cầu đến Ollama bị timeout.")
            answer = "Yêu cầu đến model Qwen bị gián đoạn (timeout)."
        except requests.RequestException as e:
            print(f"Lỗi khi gọi Ollama API: {e}")
            answer = f"lỗi khi gọi model: {e}"
        
        return {"answer": answer, "sources": sources_for_frontend}
    
    def generate_quiz(self, context_chunks: List[Dict], k: int) -> Dict:
        if not self.is_ready():
            return {"status": "error", "message": "Lỗi: Model Qwen (Ollama) chưa sẵn sàng."}

        prompt = super()._create_quiz_prompt(context_chunks, k)

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2,
                "num_ctx": 4096
            }
        }
        
        print(f"\nGửi yêu cầu (quiz) đến Ollama({self.model_name}) (yêu cầu JSON)...")
        try:
            response = self.session.post(self.api_url, json=payload, timeout=180) # Tăng timeout
            response.raise_for_status()
            
            response_json = response.json()
            json_text = response_json.get("response")

            if not json_text:
                return {"status": "error", "message": "Lỗi: Ollama trả về JSON nhưng không có 'response'."}
            questions_list = json.loads(json_text)
            print(f"Ollama đã trả về {len(questions_list)} câu hỏi trắc nghiệm.")
            
            return {"status": "success", "questions": questions_list}

        except json.JSONDecodeError as e:
            print(f"Ollama không trả về JSON hợp lệ. Lỗi: {e}")
            print(f"Nội dung trả về: {json_text[:500]}...")
            return {"status": "error", "message": "dữ liệu không đúng định dạng JSON."}
        except requests.Timeout:
            print("Lỗi: Yêu cầu (quiz) đến Ollama bị timeout.")
            return {"status": "error", "message": "Yêu cầu đến model Qwen bị gián đoạn (timeout)."}
        except requests.RequestException as e:
            print(f"Lỗi khi gọi Ollama (quiz): {e}")
            return {"status": "error", "message": f"Đã xảy ra lỗi khi gọi model Qwen: {e}"}