
// export type Role = 'user' | 'model' | 'error';

// export interface Message {
//   id: string;
//   role: Role;
//   content: string;
// }

// export const AVAILABLE_MODELS = {
//   'gemini-2.5-flash': 'Gemini 2.5 Flash',
// };

// // Định nghĩa cấu trúc của một nguồn (source)
// export interface Source {
//     id: string;
//     hierarchy: string;
//     content_preview: string;
// }

// // Định nghĩa cấu trúc của đối tượng response từ API
// export interface ChatResponse {
//     answer: string;
//     sources: Source[];
// }

// ============ NEW CONTENT ===========
// Định nghĩa cấu trúc của một nguồn (source)
export interface Source {
    id: string;
    hierarchy: string;
    content_preview: string;
}

// Định nghĩa cấu trúc của đối tượng response từ API
export interface ChatResponse {
    answer: string;
    sources: Source[];
}

// <<< MỚI: Thêm các type cho Chế độ Trắc nghiệm (Quiz Mode) >>>

// Định nghĩa các model (chuyển từ geminiService.ts sang đây)
export type ModelOption = 'gemini' | 'qwen';

// Cấu trúc 1 câu hỏi JSON thô nhận từ API (như backend đã định nghĩa)
export interface ApiQuizQuestion {
    question: string;
    options: {
        A: string;
        B: string;
        C: string;
        D: string;
    };
    correct_answer: string; // 'A', 'B', 'C', or 'D'
}

// Cấu trúc 1 câu hỏi ở giao diện (thêm 'id' để React render)
export interface UiQuizQuestion extends ApiQuizQuestion {
    id: string;
}

// Cấu trúc response khi gọi API /generate_quiz thành công
export interface QuizSuccessResponse {
    status: 'success';
    questions: ApiQuizQuestion[]; // API trả về mảng câu hỏi thô
}

// Cấu trúc response khi gọi API /generate_quiz thất bại
export interface QuizErrorResponse {
    status: 'error';
    message: string;
}

// Kiểu dữ liệu (Union type) của API trắc nghiệm
export type QuizApiResponse = QuizSuccessResponse | QuizErrorResponse;
// <<< HẾT PHẦN MỚI >>>
