import React, { useState, useRef, useEffect, useCallback } from 'react';
// SỬA LỖI: Đường dẫn đúng phải là './' vì App.tsx và services/ là cùng cấp
import { getChatbotResponse } from './services/geminiService';
import type { Message, Role, Source } from './types';

// --- Icon Components (Giữ nguyên) --- //
const BotIcon: React.FC<{ className?: string }> = ({ className = "w-6 h-6" }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zM8.5 12c.83 0 1.5-.67 1.5-1.5S9.33 9 8.5 9 7 9.67 7 10.5 7.67 12 8.5 12zm7 0c.83 0 1.5-.67 1.5-1.5S16.33 9 15.5 9s-1.5.67-1.5 1.5.67 1.5 1.5 1.5zM12 16.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z" /></svg>
);
const UserIcon: React.FC<{ className?: string }> = ({ className = "w-6 h-6" }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" /></svg>
);
const SendIcon: React.FC<{ className?: string }> = ({ className = "w-6 h-6" }) => (
    <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" /></svg>
);

// --- UI Components --- //

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

// --- Main App Component --- //

export default function App() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 'init',
            role: 'model',
            content: 'Xin chào! Hãy hỏi tôi về Lịch sử Việt Nam giai đoạn 1954-1975.',
        },
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const chatEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isLoading]);

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
            const response = await getChatbotResponse(currentInput);

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
    }, [input, isLoading]);

    const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex flex-col h-screen bg-slate-900 text-slate-100 font-sans">
            <header className="bg-slate-800/50 backdrop-blur-sm p-4 border-b border-slate-700 shadow-lg z-10">
                <div className="container mx-auto flex justify-center items-center">
                    <h1 className="text-xl font-bold text-white">History Chatbot RAG</h1>
                </div>
            </header>

            <main className="flex-1 overflow-y-auto p-4">
                <div className="container mx-auto max-w-4xl">
                    {messages.map((msg) => (<ChatMessage key={msg.id} message={msg} />))}
                    {isLoading && <LoadingIndicator />}
                    <div ref={chatEndRef} />
                </div>
            </main>

            <footer className="bg-slate-800 p-4 border-t border-slate-700">
                <div className="container mx-auto max-w-4xl">
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
                </div>
            </footer>
        </div>
    );
}
