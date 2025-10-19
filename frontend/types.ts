
// export type Role = 'user' | 'model' | 'error';

// export interface Message {
//   id: string;
//   role: Role;
//   content: string;
// }

// export const AVAILABLE_MODELS = {
//   'gemini-2.5-flash': 'Gemini 2.5 Flash',
// };

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
