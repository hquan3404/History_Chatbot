import { ChatResponse } from "../types"; // Import cấu trúc dữ liệu đã định nghĩa

// Địa chỉ của backend FastAPI đang chạy trên máy của bạn
const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * Gửi câu hỏi đến backend RAG và nhận lại câu trả lời hoàn chỉnh.
 * @param query Câu hỏi của người dùng.
 * @param top_k Số lượng chunk liên quan cần truy xuất.
 * @returns Một promise chứa câu trả lời và các nguồn tham khảo.
 */
export const getChatbotResponse = async (query: string, top_k: number = 5): Promise<ChatResponse> => {
    console.log(`Sending query to backend: "${query}"`);

    try {
        // Gọi đến endpoint /api/v1/chat bằng phương thức POST
        const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            // Gửi body theo đúng cấu trúc QueryRequest trong file main.py
            body: JSON.stringify({
                query: query,
                top_k: top_k,
            }),
        });

        // Kiểm tra nếu request không thành công (vd: lỗi 500)
        if (!response.ok) {
            // Đọc lỗi chi tiết từ server và ném ra để xử lý ở giao diện
            const errorData = await response.json();
            throw new Error(errorData.detail || `Lỗi từ server: ${response.statusText}`);
        }

        // Nếu thành công, đọc dữ liệu JSON trả về
        const data = await response.json();
        
        // Trả về phần `response` của dữ liệu, có cấu trúc khớp với ChatResponse
        return data.response;

    } catch (error) {
        console.error("Lỗi khi gọi API backend:", error);
        
        // Ném lỗi ra ngoài để component có thể bắt và hiển thị cho người dùng
        if (error instanceof Error) {
            throw new Error(`Không thể kết nối đến server: ${error.message}`);
        }
        throw new Error("Đã xảy ra lỗi không xác định khi kết nối đến server.");
    }
};