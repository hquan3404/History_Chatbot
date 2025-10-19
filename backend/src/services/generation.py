import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from typing import List, Dict

# Import các biến cấu hình trực tiếp
from src.core.config import GEMINI_API_KEY, GENERATION_MODEL_NAME

class GeminiRAGGenerator:
    def __init__(self):
        """
        Khởi tạo module, cấu hình API key và model.
        """
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            
            # Cấu hình an toàn để tránh bị chặn không cần thiết
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
            
            # Cấu hình cho việc sinh văn bản
            self.generation_config = {
                "temperature": 0.1,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 8192, # Tăng giới hạn token đầu ra
            }
            print("Khởi tạo Gemini model thành công!")

        except Exception as e:
            print(f"Lỗi nghiêm trọng khi khởi tạo Gemini model: {e}")
            self.model = None

    def _create_prompt(self, query: str, context_chunks: List[Dict]) -> str:
        """
        Tạo một prompt hoàn chỉnh cho LLM từ câu hỏi và các chunk ngữ cảnh.
        """
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

    def generate_answer(self, query: str, context_chunks: List[Dict]) -> Dict:
        """
        Sinh câu trả lời từ model một cách an toàn và in thông tin debug chi tiết.
        """
        if not self.model:
            return {"answer": "Lỗi: Model chưa được khởi tạo.", "sources": []}

        # Logging chi tiết các chunk và điểm số
        print("\n" + "="*80)
        print(f"Đã truy vấn được {len(context_chunks)} chunks cho câu hỏi: '{query}'")
        
        unique_sources_paths = set()
        for i, chunk in enumerate(context_chunks):
            source_path = chunk.get("metadata", {}).get("hierarchy_path", "N/A")
            unique_sources_paths.add(source_path)
            
            # Trích xuất các điểm số một cách an toàn
            final_score = chunk.get("final_score", 0.0)
            rerank_score = chunk.get("rerank_score", 0.0)
            combined_score = chunk.get("combined_score", 0.0)
            semantic_score = chunk.get("semantic_score", 0.0)
            keyword_score = chunk.get("keyword_score", 0.0)

            print(f"\n--- Chunk {i+1} (Rank: {chunk.get('rank', 'N/A')}) ---")
            print(f"  - Nguồn          : {source_path}")
            print(f"  - Điểm số cuối cùng: {final_score:.4f}")
            print(f"      ├─ Rerank    : {rerank_score:.4f}")
            print(f"      ├─ Combined  : {combined_score:.4f}")
            print(f"      │   ├─ Semantic: {semantic_score:.4f} (vector search)")
            print(f"      │   └─ Keyword : {keyword_score:.4f} (BM25)")
            print(f"  - Nội dung        : \"{chunk.get('content', '')[:250]}...\"")
        
        print("\n" + "="*80)
        print("Nguồn chính được sử dụng để tổng hợp câu trả lời:")
        if unique_sources_paths:
            for source in sorted(list(unique_sources_paths)):
                print(f"  - {source}")
        else:
            print("  Không có nguồn cụ thể nào được tìm thấy.")
        print("="*80)

        prompt = self._create_prompt(query, context_chunks)
        
        sources_for_frontend = [
            {
                "id": chunk["chunk_id"],
                "hierarchy": chunk.get("metadata", {}).get("hierarchy_path", "N/A"),
                "content_preview": chunk.get("content", "")[:150] + "..."
            }
            for chunk in context_chunks
        ]
        
        print("\nGửi yêu cầu đến Gemini API và chờ câu trả lời...")
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            if response.parts:
                answer = "".join(part.text for part in response.parts)
                print("Gemini đã trả về câu trả lời.")
                if response.candidates[0].finish_reason.name == "MAX_TOKENS":
                    answer += "\n\n...(Phản hồi có thể đã bị cắt ngắn do đạt đến giới hạn độ dài tối đa)..."
            else:
                finish_reason = response.candidates[0].finish_reason.name
                print(f"Gemini không trả về nội dung. Lý do: {finish_reason}")
                answer = f"Rất tiếc, không thể tạo câu trả lời. Lý do từ API: {finish_reason}"

        except Exception as e:
            print(f"Lỗi khi gọi Gemini API: {e}")
            answer = f"Đã xảy ra lỗi khi gọi Gemini API: {e}"

        return {"answer": answer, "sources": sources_for_frontend}

