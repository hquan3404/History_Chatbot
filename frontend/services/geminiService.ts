// <<< THAY ĐỔI: Import thêm các type mới từ types.ts >>>
import { 
    ChatResponse, 
    ModelOption, 
    QuizApiResponse 
} from "../types";

// Địa chỉ của backend FastAPI đang chạy trên máy của bạn
const API_BASE_URL = "http://127.0.0.1:8000";

// <<< THAY ĐỔI: Xóa 'ModelOption' khỏi file này vì đã chuyển sang types.ts >>>
// export type ModelOption = 'gemini' | 'qwen'; // ĐÃ CHUYỂN

/**
 * Gửi câu hỏi đến backend RAG và nhận lại câu trả lời hoàn chỉnh.
 * (Hàm này giữ nguyên)
 */
export const getChatbotResponse = async (
    query: string, 
    model: ModelOption,
    top_k: number = 5
): Promise<ChatResponse> => {
    console.log(`Sending query to backend: "${query}" using model: "${model}"`);

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                top_k: top_k,
                model: model,
            }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Lỗi từ server: ${response.statusText}`);
        }

        const data = await response.json();
        return data.response;

    } catch (error) {
        console.error("Lỗi khi gọi API backend:", error);
        if (error instanceof Error) {
            throw new Error(`Không thể kết nối đến server: ${error.message}`);
        }
        throw new Error("Đã xảy ra lỗi không xác định khi kết nối đến server.");
    }
};

// <<< MỚI: Thêm hàm để gọi API sinh câu hỏi trắc nghiệm >>>
/**
 * Gửi yêu cầu tạo câu hỏi trắc nghiệm đến backend.
 * @param topic Chủ đề (tùy chọn) để tìm ngữ cảnh.
 * @param k Số lượng câu hỏi cần tạo.
 * @param model Model được chọn ('gemini' hoặc 'qwen').
 * @returns Một promise chứa mảng các câu hỏi hoặc một lỗi.
 */
export const generateQuizQuestions = async (
    topic: string,
    k: number,
    model: ModelOption
): Promise<QuizApiResponse> => {
    console.log(`Sending quiz request: topic="${topic}", k=${k}, model="${model}"`);

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/generate_quiz`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            // Gửi body theo đúng cấu trúc QuizRequest trong file main.py
            body: JSON.stringify({
                topic: topic,
                k: k,
                model: model,
            }),
        });

        // API trả về JSON (thành công hoặc lỗi) ngay cả khi !response.ok
        const data: QuizApiResponse = await response.json();

        if (!response.ok) {
            // Nếu là lỗi (vd: 500, 400) và có cấu trúc lỗi
            if (data.status === 'error') {
                throw new Error(data.message || `Lỗi từ server: ${response.statusText}`);
            }
            // Lỗi không xác định
            throw new Error(`Lỗi từ server: ${response.statusText}`);
        }

        // Nếu response.ok và có status 'success'
        if (data.status === 'success') {
            return data;
        } else {
            // Trường hợp response.ok nhưng API vẫn báo lỗi (hiếm gặp)
            throw new Error((data as any).message || "Lỗi không xác định từ API.");
        }

    } catch (error) {
        console.error("Lỗi khi gọi API tạo trắc nghiệm:", error);
        if (error instanceof Error) {
            throw new Error(`Không thể kết nối đến server: ${error.message}`);
        }
        throw new Error("Đã xảy ra lỗi không xác định khi kết nối đến server.");
    }
};
// <<< HẾT PHẦN MỚI >>>

