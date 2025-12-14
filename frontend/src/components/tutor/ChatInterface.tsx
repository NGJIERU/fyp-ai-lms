"use client";

import { useEffect, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";

export type ChatMessage = {
    role: "user" | "assistant";
    content: string;
    sources?: { title: string; url?: string; source?: string }[];
};

type ChatInterfaceProps = {
    courseId: number;
    initialMessage?: string;
    onClose?: () => void;
};

export default function ChatInterface({ courseId, initialMessage, onClose }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState(initialMessage || "");
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    async function handleSend(e?: React.FormEvent) {
        e?.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMsg: ChatMessage = { role: "user", content: input };
        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setIsLoading(true);

        try {
            // Prepare history (limit to last 10 messages to keep payload reasonable)
            const history = messages.slice(-10).map(m => ({
                role: m.role,
                content: m.content
            }));

            const response = await apiFetch<{ response: string; sources: any[] }>(`/api/v1/tutor/chat?course_id=${courseId}`, {
                method: "POST",
                body: JSON.stringify({
                    message: userMsg.content,
                    conversation_history: history,
                }),
            });

            const aiMsg: ChatMessage = {
                role: "assistant",
                content: response.response,
                sources: response.sources,
            };
            setMessages((prev) => [...prev, aiMsg]);
        } catch (err) {
            console.error("Chat error:", err);
            // Add error message
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "Sorry, I encountered an error. Please try again." },
            ]);
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div className="flex h-full flex-col bg-white">
            {/* Header - nice to have in standalone, but if embedded, maybe minimal? */}
            <div className="flex items-center justify-between border-b border-gray-100 p-4">
                <div>
                    <h2 className="text-lg font-semibold text-gray-900">AI Personal Tutor</h2>
                    <p className="text-xs text-gray-500">Ask anything about this course</p>
                </div>
                {onClose && (
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                        ✕
                    </button>
                )}
            </div>

            <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-6">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 text-center text-gray-500">
                        <div className="mb-4 rounded-full bg-indigo-50 p-4">
                            <span className="text-3xl">👋</span>
                        </div>
                        <p className="font-medium text-gray-900">Start a conversation</p>
                        <p className="text-sm">Ask about any topic, concept, or material in this course.</p>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"
                            }`}
                    >
                        <div
                            className={`max-w-[85%] rounded-2xl px-5 py-3.5 shadow-sm ${msg.role === "user"
                                ? "bg-indigo-600 text-white"
                                : "bg-gray-100 text-gray-800"
                                }`}
                        >
                            <div className="whitespace-pre-wrap text-sm leading-relaxed">
                                {msg.content}
                            </div>

                            {msg.sources && msg.sources.length > 0 && (
                                <div className={`mt-3 border-t pt-2 text-xs ${msg.role === "user" ? "border-indigo-500/30 text-indigo-100" : "border-gray-200 text-gray-500"
                                    }`}>
                                    <p className="mb-1 font-semibold uppercase opacity-70">Sources:</p>
                                    <div className="flex flex-wrap gap-2">
                                        {msg.sources.map((src, i) => (
                                            <a
                                                key={i}
                                                href={src.url || "#"}
                                                target="_blank"
                                                rel="noreferrer"
                                                className={`underline decoration-dotted hover:decoration-solid ${msg.role === "user" ? "hover:text-white" : "hover:text-indigo-600"
                                                    }`}
                                            >
                                                {src.title}
                                            </a>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="rounded-2xl bg-gray-50 px-5 py-4 text-gray-500">
                            <div className="flex space-x-1.5">
                                <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.3s]"></div>
                                <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.15s]"></div>
                                <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400"></div>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <div className="border-t border-gray-100 p-4">
                <form onSubmit={handleSend} className="relative flex items-center gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Type your question..."
                        className="flex-1 rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 pr-12 text-sm focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || isLoading}
                        className="absolute right-2 rounded-lg bg-indigo-600 p-2 text-white transition hover:bg-indigo-700 disabled:opacity-50"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
                            <path d="M3.105 2.289a.75.75 0 00-.826.95l1.414 4.925A1.5 1.5 0 005.135 9.25h6.115a.75.75 0 010 1.5H5.135a1.5 1.5 0 00-1.442 1.086l-1.414 4.926a.75.75 0 00.826.95 28.896 28.896 0 0015.293-7.154.75.75 0 000-1.115A28.897 28.897 0 003.105 2.289z" />
                        </svg>
                    </button>
                </form>
            </div>
        </div>
    );
}
