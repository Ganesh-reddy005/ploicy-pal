"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Loader2, FileText, Sparkles, AlertCircle, Network } from "lucide-react";
import CitationCard from "./CitationCard";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  timestamp: Date;
}

interface Citation {
  section_id: string;
  clause_name: string;
  text_snippet: string;
}

interface ChatSectionProps {
  documentId: string;
  onNewDocument: () => void;
  onViewGraph: () => void;
}

export default function ChatSection({ documentId, onNewDocument, onViewGraph }: ChatSectionProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    const currentInput = input;
    setInput("");

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/chat`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question: currentInput,
            document_id: documentId,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Failed to get response");
      }

      const assistantMessage: Message = {
        role: "assistant",
        content: data.answer,
        citations: data.citations || [],
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleNewChat = () => {
    onNewDocument();
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="flex flex-col h-[calc(100vh-220px)] min-h-[500px] bg-white rounded-xl border border-gray-100 overflow-hidden">
      {/* Chat Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 bg-gray-50/50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gray-900 rounded-lg flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-medium text-gray-900">PolicyPal Assistant</h2>
            <p className="text-xs text-gray-400">Ask questions about your policy</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onViewGraph}
            className="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors flex items-center gap-1"
            title="View Knowledge Graph"
          >
            <Network className="w-4 h-4" />
            Graph
          </button>
          <button
            onClick={handleNewChat}
            className="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            New Document
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <Sparkles className="w-5 h-5 text-gray-600" />
            </div>
            <h3 className="text-base font-medium text-gray-900 mb-2">
              How can I help you?
            </h3>
            <p className="text-sm text-gray-400 max-w-xs mb-6">
              Ask me anything about your policy - coverage, exclusions, waiting periods, claims process, etc.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {[
                "What does this policy cover?",
                "Are pre-existing conditions covered?",
                "What's the waiting period?",
                "How do I file a claim?",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => {
                    setInput(suggestion);
                    textareaRef.current?.focus();
                  }}
                  className="px-3 py-1.5 text-xs bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index} className={`flex gap-3 ${message.role === "user" ? "flex-row-reverse" : ""}`}>
            <div
              className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${
                message.role === "user"
                  ? "bg-gray-200"
                  : "bg-gray-900"
              }`}
            >
              {message.role === "user" ? (
                <FileText className="w-3.5 h-3.5 text-gray-600" />
              ) : (
                <Sparkles className="w-3.5 h-3.5 text-white" />
              )}
            </div>
            <div
              className={`flex-1 max-w-[80%] ${
                message.role === "user" ? "text-right" : "text-left"
              }`}
            >
              <div
                className={`inline-block px-4 py-2.5 rounded-2xl ${
                  message.role === "user"
                    ? "bg-gray-900 text-white rounded-tr-sm"
                    : "bg-gray-50 text-gray-900 rounded-tl-sm"
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              </div>
              <p className="text-xs text-gray-300 mt-1.5 px-1">{formatTime(message.timestamp)}</p>

              {/* Citations */}
              {message.citations && message.citations.length > 0 && (
                <div className="mt-3 animate-slide-down">
                  <p className="text-xs font-medium text-gray-400 mb-2">
                    Sources cited:
                  </p>
                  <div className="space-y-2">
                    {message.citations.map((citation, citeIndex) => (
                      <CitationCard key={citeIndex} citation={citation} index={citeIndex} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gray-900 flex items-center justify-center">
              <Sparkles className="w-3.5 h-3.5 text-white" />
            </div>
            <div className="bg-gray-50 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce-dot" style={{ animationDelay: "0ms" }} />
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce-dot" style={{ animationDelay: "160ms" }} />
                <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce-dot" style={{ animationDelay: "320ms" }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error Toast */}
      {error && (
        <div className="mx-5 mb-4 p-3 bg-red-50 border border-red-100 rounded-lg flex items-center gap-2 text-red-600 animate-slide-down">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span className="text-sm">{error}</span>
          <button
            onClick={() => setError(null)}
            className="ml-auto text-red-400 hover:text-red-700 text-lg leading-none"
          >
            ×
          </button>
        </div>
      )}

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-100 bg-gray-50/50">
        <div className="flex items-end gap-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your policy..."
            rows={1}
            disabled={isLoading}
            className="flex-1 px-4 py-3 bg-white border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:border-gray-400 resize-none transition-colors min-h-[48px] max-h-32 text-sm"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="flex-shrink-0 p-3 bg-gray-900 text-white rounded-xl hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Send message"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
        <p className="text-xs text-gray-300 text-center mt-2">
          Press Enter to send • Shift+Enter for new line
        </p>
      </form>
    </div>
  );
}