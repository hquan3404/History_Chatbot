import React, { useState, useRef, useEffect, useCallback } from 'react';
// <<< THAY ĐỔI: Import thêm hàm/type mới từ service và types >>>
import { 
    getChatbotResponse, 
    generateQuizQuestions, // Mới
    ModelOption 
} from './services/geminiService.ts';
import type { 
    Message, 
    Role, 
    Source, 
    UiQuizQuestion, // Mới
    QuizApiResponse   // Mới
} from './types.ts';

// --- Icon Components --- //
const BotIcon: React.FC<{ className?: string }> = ({ className = "w-6 h-6" }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zM8.5 12c.83 0 1.5-.67 1.5-1.5S9.33 9 8.5 9 7 9.67 7 10.5 7.67 12 8.5 12zm7 0c.83 0 1.5-.67 1.5-1.5S16.33 9 15.5 9s-1.5.67-1.5 1.5.67 1.5 1.5 1.5zM12 16.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z" /></svg>
);
const UserIcon: React.FC<{ className?: string }> = ({ className = "w-6 h-6" }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" /></svg>
);
const SendIcon: React.FC<{ className?: string }> = ({ className = "w-6 h-6" }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" /></svg>
);

// <<< MỚI: Thêm icon cho 2 chế độ (mode) >>>
const ChatIcon: React.FC<{ className?: string }> = ({ className = "w-5 h-5" }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17.608 2.98 14.083A9.04 9.04 0 012 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zm-4 0H9v2h2V9z" clipRule="evenodd" /></svg>
);
const QuizIcon: React.FC<{ className?: string }> = ({ className = "w-5 h-5" }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 18c2.652 0 5.09-.693 7.166-1.874A1 1 0 0017.166 15V4.999a1 1 0 00-.834-1 11.954 11.954 0 00-7.166 1.874 1 1 0 00-.834 1zM4 7a1 1 0 011-1h.01a1 1 0 110 2H5a1 1 0 01-1-1zm3 0a1 1 0 011-1h.01a1 1 0 110 2H8a1 1 0 01-1-1zm3 0a1 1 0 011-1h.01a1 1 0 110 2H11a1 1 0 01-1-1zm3 0a1 1 0 011-1h.01a1 1 0 110 2H14a1 1 0 01-1-1z" clipRule="evenodd" /></svg>
);
// <<< HẾT PHẦN MỚI >>>

// --- UI Components --- //

// (ChatMessage và LoadingIndicator giữ nguyên)
interface ChatMessageProps {
    message: Message;
}
const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
    const { role, content, sources } = message;
    const isUser = role === 'user';
    const isError = role === 'error';
    const baseClasses = "flex items-start gap-3 my-4";
    const messageClasses = `p-4 max-w-[80%] rounded-2xl shadow-md`;
    if (isError) {
        return (
            <div className="flex justify-center">
                <div className="p-3 my-2 text-sm text-red-200 bg-red-800 bg-opacity-50 rounded-lg">
                    {content}
                </div>
            </div>
        );
    }
    return (
        <div className={`${baseClasses} ${isUser ? "justify-end" : "justify-start"}`}>
            {!isUser && <div className="p-2 bg-slate-700 rounded-full"><BotIcon className="w-6 h-6 text-slate-300" /></div>}
            <div className={`${messageClasses} ${isUser ? 'bg-blue-600 text-white rounded-br-none' : 'bg-slate-700 text-slate-200 rounded-bl-none'}`}>
                <p className="whitespace-pre-wrap">{content}</p>
                {sources && sources.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-slate-600">
                        <h4 className="font-semibold text-xs mb-2 text-slate-400">Nguồn tham khảo:</h4>
                        <ul className="list-disc list-inside text-xs space-y-1 text-slate-300">
                            {sources.map((source) => (
                                <li key={source.id}>
                                    <span className="font-medium">{source.hierarchy || 'N/A'}:</span>
                                    <em className="text-slate-400 ml-1">"{source.content_preview}"</em>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
            {isUser && <div className="p-2 bg-slate-600 rounded-full"><UserIcon className="w-6 h-6 text-slate-200" /></div>}
        </div>
    );
};
const LoadingIndicator: React.FC = () => (
    <div className="flex items-start gap-3 my-4 justify-start">
        <div className="p-2 bg-slate-700 rounded-full"><BotIcon className="w-6 h-6 text-slate-300" /></div>
        <div className="p-4 max-w-[80%] rounded-2xl shadow-md bg-slate-700 text-slate-200 rounded-bl-none">
            <div className="flex items-center gap-2">
                <span className="text-slate-400">Đang tìm kiếm và tổng hợp</span>
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse [animation-delay:-0.3s]"></div>
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse [animation-delay:-0.15s]"></div>
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-pulse"></div>
            </div>
        </div>
    </div>
);
// --- Hết Component giữ nguyên ---

// <<< MỚI: Thêm Component để hiển thị câu hỏi trắc nghiệm >>>
interface QuizQuestionCardProps {
    question: UiQuizQuestion;
    isRevealed: boolean;
    onToggleReveal: (id: string) => void;
}

const QuizQuestionCard: React.FC<QuizQuestionCardProps> = ({ question, isRevealed, onToggleReveal }) => {
    // Chuyển object options thành mảng để map
    const optionsArray = Object.entries(question.options) as [string, string][]; // [ ['A', 'Nội dung A'], ... ]

    return (
        <div className="bg-slate-800 p-6 rounded-2xl shadow-lg border border-slate-700 mb-6">
            <h3 className="text-lg font-semibold text-slate-100 mb-4">{question.question}</h3>
            <div className="space-y-3">
                {optionsArray.map(([key, value]) => {
                    const isCorrect = key === question.correct_answer;
                    const isSelectedAndWrong = isRevealed && !isCorrect;

                    // Xác định màu nền khi đã lật đáp án
                    let revealClasses = '';
                    if (isRevealed) {
                        if (isCorrect) {
                            revealClasses = 'bg-green-700 border-green-500 text-white'; // Đáp án đúng
                        } else {
                            revealClasses = 'bg-red-800 border-red-600 text-slate-300 opacity-60'; // Đáp án sai
                        }
                    } else {
                        revealClasses = 'bg-slate-700 border-slate-600 hover:bg-slate-600'; // Chưa lật
                    }

                    return (
                        <div
                            key={key}
                            className={`flex items-center gap-3 p-3 rounded-lg border transition-all ${revealClasses}`}
                        >
                            <span className={`font-bold ${isRevealed && isCorrect ? 'text-white' : 'text-slate-400'}`}>{key}:</span>
                            <span className="text-sm">{value}</span>
                        </div>
                    );
                })}
            </div>
            <div className="mt-5 text-center">
                <button
                    onClick={() => onToggleReveal(question.id)}
                    className="px-4 py-2 text-sm font-medium rounded-md bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                >
                    {isRevealed ? 'Ẩn đáp án' : 'Xem đáp án'}
                </button>
            </div>
        </div>
    );
};
// <<< HẾT PHẦN MỚI >>>

// --- Main App Component --- //

export default function App() {
    // --- State cho chế độ Chat (Giữ nguyên) ---
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 'init',
            role: 'model',
            content: 'Xin chào! Hãy chọn chế độ "Hỏi đáp" hoặc "Tạo trắc nghiệm".',
        },
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [selectedModel, setSelectedModel] = useState<ModelOption>('gemini');
    const chatEndRef = useRef<HTMLDivElement>(null);

    // <<< MỚI: Thêm State cho chế độ (Mode) và Trắc nghiệm (Quiz) >>>
    const [mode, setMode] = useState<'chat' | 'quiz'>('chat');
    const [quizK, setQuizK] = useState<number>(3); // Số câu hỏi (mặc định 3)
    const [quizTopic, setQuizTopic] = useState<string>(''); // Chủ đề (tùy chọn)
    const [quizQuestions, setQuizQuestions] = useState<UiQuizQuestion[]>([]);
    const [quizError, setQuizError] = useState<string | null>(null);
    const [revealedAnswers, setRevealedAnswers] = useState<Set<string>>(new Set());
    // <<< HẾT PHẦN MỚI >>>
    
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

    // (Hàm handleSend và handleKeyPress giữ nguyên)
    const handleSend = useCallback(async () => {
        if (!input.trim() || isLoading) return;
        const userMessage: Message = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: input,
        };
        setMessages((prev) => [...prev, userMessage]);
        const currentInput = input;
        setInput('');
        setIsLoading(true);
        try {
            const response = await getChatbotResponse(currentInput, selectedModel);
            const modelMessage: Message = {
                id: `model-${Date.now()}`,
                role: 'model',
                content: response.answer,
                sources: response.sources,
            };
            setMessages((prev) => [...prev, modelMessage]);
        } catch (error) {
            console.error("Lỗi khi gửi yêu cầu:", error);
            const errorMessage: Message = {
                id: `error-${Date.now()}`,
                role: 'error',
                content: error instanceof Error ? error.message : "Lỗi không xác định",
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    }, [input, isLoading, selectedModel]);
    const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };
    // --- Hết phần giữ nguyên ---

    // <<< MỚI: Hàm xử lý khi nhấn nút tạo trắc nghiệm >>>
    const handleGenerateQuiz = useCallback(async () => {
        setIsLoading(true);
        setQuizError(null);
        setQuizQuestions([]); // Xóa câu hỏi cũ
        setRevealedAnswers(new Set()); // Đặt lại đáp án

        try {
            // Gọi API mới
            const response = await generateQuizQuestions(quizTopic, quizK, selectedModel);
            
            // Backend trả về response.status === 'success'
            // Chuyển đổi ApiQuizQuestion thành UiQuizQuestion (thêm id)
            const uiQuestions = response.questions.map((q, i) => ({
                ...q,
                id: `q-${Date.now()}-${i}` // Tạo id duy nhất cho React key
            }));
            setQuizQuestions(uiQuestions);

        } catch (error) {
            console.error("Lỗi khi tạo trắc nghiệm:", error);
            setQuizError(error instanceof Error ? error.message : "Lỗi không xác định");
        } finally {
            setIsLoading(false);
        }
    }, [quizTopic, quizK, selectedModel]); // Phụ thuộc vào 3 state

    // <<< MỚI: Hàm xử lý lật/ẩn đáp án >>>
    const handleToggleReveal = (id: string) => {
        setRevealedAnswers(prev => {
            const newSet = new Set(prev);
            if (newSet.has(id)) {
                newSet.delete(id);
            } else {
                newSet.add(id);
            }
            return newSet;
        });
    };
    // <<< HẾT PHẦN MỚI >>>

    return (
        <div className="flex flex-col h-screen bg-slate-900 text-slate-100 font-sans">
            <header className="bg-slate-800/50 backdrop-blur-sm p-4 border-b border-slate-700 shadow-lg z-10">
                <div className="container mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
                    <h1 className="text-xl font-bold text-white">History Chatbot RAG</h1>
                    
                    {/* <<< MỚI: Nút chọn Chế độ (Mode) >>> */}
                    <div className="flex items-center gap-2 p-1 bg-slate-700 rounded-lg">
                        <button
                            onClick={() => setMode('chat')}
                            disabled={isLoading}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                                mode === 'chat' ? 'bg-blue-600 text-white shadow' : 'text-slate-300 hover:bg-slate-600'
                            } disabled:opacity-50`}
                        >
                            <ChatIcon />
                            Hỏi đáp
                        </button>
                        <button
                            onClick={() => setMode('quiz')}
                            disabled={isLoading}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                                mode === 'quiz' ? 'bg-purple-600 text-white shadow' : 'text-slate-300 hover:bg-slate-600'
                            } disabled:opacity-50`}
                        >
                            <QuizIcon />
                            Tạo trắc nghiệm
                        </button>
                    </div>
                    {/* <<< HẾT PHẦN MỚI >>> */}

                </div>
            </header>

            {/* <<< THAY ĐỔI: Hiển thị có điều kiện (Conditional Rendering) cho <main> >>> */}
            <main className="flex-1 overflow-y-auto p-4">
                <div className="container mx-auto max-w-4xl">
                    
                    {/* --- CHẾ ĐỘ HỎI ĐÁP (CHAT MODE) --- */}
                    {mode === 'chat' && (
                        <>
                            {messages.map((msg) => (<ChatMessage key={msg.id} message={msg} />))}
                            {isLoading && <LoadingIndicator />}
                            <div ref={chatEndRef} />
                        </>
                    )}

                    {/* --- CHẾ ĐỘ TRẮC NGHIỆM (QUIZ MODE) --- */}
                    {mode === 'quiz' && (
                        <div>
                            {/* Hiển thị lỗi (nếu có) */}
                            {quizError && (
                                <div className="flex justify-center">
                                    <div className="p-3 my-2 text-sm text-red-200 bg-red-800 bg-opacity-50 rounded-lg">
                                        {quizError}
                                    </div>
                                </div>
                            )}
                            
                            {/* Hiển thị loading */}
                            {isLoading && (
                                <div className="text-center text-slate-400 py-10">
                                    Đang tạo câu hỏi...
                                </div>
                            )}

                            {/* Hiển thị danh sách câu hỏi */}
                            {!isLoading && quizQuestions.length > 0 && (
                                <div className="space-y-6">
                                    {quizQuestions.map(q => (
                                        <QuizQuestionCard
                                            key={q.id}
                                            question={q}
                                            isRevealed={revealedAnswers.has(q.id)}
                                            onToggleReveal={handleToggleReveal}
                                        />
                                    ))}
                                </div>
                            )}

                            {/* Hướng dẫn ban đầu */}
                            {!isLoading && quizQuestions.length === 0 && !quizError && (
                                <div className="text-center text-slate-500 py-20 px-6 bg-slate-800 rounded-2xl">
                                    <h2 className="text-lg font-semibold text-slate-300">Chế độ Tạo trắc nghiệm</h2>
                                    <p className="mt-2">Nhập chủ đề (hoặc để trống) và số lượng câu hỏi ở bên dưới, sau đó nhấn "Tạo".</p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </main>
            {/* <<< HẾT PHẦN THAY ĐỔI >>> */}


            <footer className="bg-slate-800 p-4 border-t border-slate-700">
                <div className="container mx-auto max-w-4xl">
                    
                    {/* <<< THAY ĐỔI: Hiển thị có điều kiện cho <footer> >>> */}
                    
                    {/* --- FOOTER CHẾ ĐỘ CHAT --- */}
                    {mode === 'chat' && (
                        <>
                            {/* Khối chọn Model */}
                            <div className="flex justify-center items-center gap-6 mb-4">
                                <span className="text-sm font-medium text-slate-300">Sử dụng model:</span>
                                <div className="flex gap-4">
                                    {/* Nút chọn Gemini */}
                                    <label className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors
                                        ${selectedModel === 'gemini' ? 'bg-blue-600 text-white shadow-md' : 'bg-slate-600 text-slate-200'} 
                                        ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-slate-500'}
                                    `}>
                                        <input
                                            type="radio" name="model" value="gemini"
                                            checked={selectedModel === 'gemini'}
                                            onChange={() => setSelectedModel('gemini')}
                                            className="w-4 h-4 text-blue-400 bg-slate-700 border-slate-500 focus:ring-blue-500"
                                            disabled={isLoading}
                                        />
                                        <span className="text-sm font-semibold">API Gemini</span>
                                    </label>
                                    
                                    {/* Nút chọn Qwen */}
                                    <label className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors
                                        ${selectedModel === 'qwen' ? 'bg-green-600 text-white shadow-md' : 'bg-slate-600 text-slate-200'} 
                                        ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-slate-500'}
                                    `}>
                                        <input
                                            type="radio" name="model" value="qwen"
                                            checked={selectedModel === 'qwen'}
                                            onChange={() => setSelectedModel('qwen')}
                                            className="w-4 h-4 text-green-400 bg-slate-700 border-slate-500 focus:ring-green-500"
                                            disabled={isLoading}
                                        />
                                        <span className="text-sm font-semibold">Qwen 1.7B (Local)</span>
                                    </label>
                                </div>
                            </div>

                            {/* Khối input chat */}
                            <div className="flex items-center bg-slate-700 rounded-xl p-2">
                                <textarea
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyPress={handleKeyPress}
                                    placeholder="Nhập câu hỏi của bạn ở đây..."
                                    rows={1}
                                    className="flex-1 bg-transparent resize-none focus:outline-none p-2 text-slate-100 placeholder-slate-400"
                                    disabled={isLoading}
                                />
                                <button
                                    onClick={handleSend}
                                    disabled={isLoading || !input.trim()}
                                    className="p-3 rounded-lg bg-blue-600 text-white disabled:bg-slate-600 disabled:cursor-not-allowed hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    aria-label="Send message"
                                >
                                    <SendIcon className="w-5 h-5" />
                                </button>
                            </div>
                        </>
                    )}

                    {/* --- FOOTER CHẾ ĐỘ TRẮC NGHIỆM --- */}
                    {mode === 'quiz' && (
                        <div className="space-y-4">
                            {/* Khối chọn Model (Tương tự ở trên, nhưng dùng cho quiz) */}
                            <div className="flex justify-center items-center gap-6">
                                <span className="text-sm font-medium text-slate-300">Sử dụng model:</span>
                                <div className="flex gap-4">
                                    <label className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${selectedModel === 'gemini' ? 'bg-blue-600 text-white' : 'bg-slate-600 text-slate-200'} ${isLoading ? 'opacity-50' : 'hover:bg-slate-500'}`}>
                                        <input type="radio" name="model" value="gemini" checked={selectedModel === 'gemini'} onChange={() => setSelectedModel('gemini')} className="w-4 h-4 text-blue-400" disabled={isLoading} />
                                        <span className="text-sm font-semibold">API Gemini</span>
                                    </label>
                                    <label className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${selectedModel === 'qwen' ? 'bg-green-600 text-white' : 'bg-slate-600 text-slate-200'} ${isLoading ? 'opacity-50' : 'hover:bg-slate-500'}`}>
                                        <input type="radio" name="model" value="qwen" checked={selectedModel === 'qwen'} onChange={() => setSelectedModel('qwen')} className="w-4 h-4 text-green-400" disabled={isLoading} />
                                        <span className="text-sm font-semibold">Qwen 1.7B (Local)</span>
                                    </label>
                                </div>
                            </div>

                            {/* Khối điều khiển tạo Quiz */}
                            <div className="flex flex-col sm:flex-row items-center gap-3 bg-slate-700 rounded-xl p-3">
                                <input
                                    type="text"
                                    value={quizTopic}
                                    onChange={(e) => setQuizTopic(e.target.value)}
                                    placeholder="Nhập chủ đề (hoặc để trống)"
                                    className="flex-1 w-full sm:w-auto bg-slate-600 rounded-lg focus:outline-none p-2.5 text-slate-100 placeholder-slate-400 focus:ring-2 focus:ring-purple-500"
                                    disabled={isLoading}
                                />
                                <div className="flex items-center gap-2">
                                    <label htmlFor="quiz-k" className="text-sm font-medium text-slate-300">Số câu:</label>
                                    <input
                                        type="number"
                                        id="quiz-k"
                                        value={quizK}
                                        onChange={(e) => setQuizK(Math.max(1, parseInt(e.target.value) || 1))}
                                        min="1"
                                        max="10"
                                        className="w-20 bg-slate-600 rounded-lg focus:outline-none p-2.5 text-slate-100 focus:ring-2 focus:ring-purple-500"
                                        disabled={isLoading}
                                    />
                                </div>
                                <button
                                    onClick={handleGenerateQuiz}
                                    disabled={isLoading}
                                    className="w-full sm:w-auto px-5 py-2.5 rounded-lg bg-purple-600 text-white font-semibold disabled:bg-slate-600 disabled:cursor-not-allowed hover:bg-purple-700 transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500"
                                >
                                    Tạo câu hỏi
                                </button>
                            </div>
                        </div>
                    )}
                    {/* <<< HẾT PHẦN THAY ĐỔI >>> */}

                </div>
            </footer>
        </div>
    );
}

