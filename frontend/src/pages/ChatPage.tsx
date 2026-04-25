import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { sendMessageStream } from '../api/chat';
import { ChatMessage } from '../components/ChatMessage';
import { Layout } from '../components/Layout';
import type { Source } from '../api/chat';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  isStreaming?: boolean;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I can answer questions about your company policy documents. What would you like to know?',
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = useCallback(async () => {
    const question = input.trim();
    if (!question || isLoading) return;

    setInput('');
    setError(null);

    const userMsgId = Date.now().toString();
    const assistantMsgId = (Date.now() + 1).toString();

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: 'user', content: question },
      { id: assistantMsgId, role: 'assistant', content: '', isStreaming: true },
    ]);
    setIsLoading(true);

    await sendMessageStream(
      question,
      (token) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, content: m.content + token }
              : m,
          ),
        );
      },
      (sources) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, isStreaming: false, sources }
              : m,
          ),
        );
        setIsLoading(false);
      },
      (errorMsg) => {
        setError(errorMsg);
        setMessages((prev) => prev.filter((m) => m.id !== assistantMsgId));
        setIsLoading(false);
      },
    );
  }, [input, isLoading]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Layout>
      <div className="max-w-3xl mx-auto flex flex-col h-[calc(100vh-65px)]">
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg) => (
            <div key={msg.id}>
              {msg.isStreaming && msg.content === '' ? (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                    <Loader2 size={16} className="text-gray-500 animate-spin" />
                  </div>
                  <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                    <div className="flex gap-1 items-center h-4">
                      <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              ) : (
                <>
                  <ChatMessage
                    role={msg.role}
                    content={msg.content}
                    sources={msg.sources}
                  />
                  {msg.isStreaming && msg.content && (
                    <span className="inline-block w-2 h-4 ml-1 bg-gray-500 animate-pulse rounded-sm align-middle" />
                  )}
                </>
              )}
            </div>
          ))}
          {error && (
            <p className="text-center text-sm text-red-500">{error}</p>
          )}
          <div ref={bottomRef} />
        </div>
        <div className="border-t border-gray-200 bg-white p-4">
          <div className="flex gap-3 items-end">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about company policy..."
              rows={1}
              className="flex-1 resize-none rounded-xl border border-gray-300 py-3 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#29ABE2] focus:border-[#29ABE2] transition-all max-h-32"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="p-3 bg-[#29ABE2] hover:bg-[#2196cc] text-white rounded-xl transition-all duration-200 disabled:opacity-40 flex-shrink-0"
            >
              <Send size={18} />
            </button>
          </div>
          <p className="text-xs text-gray-400 mt-2 text-center">
            Press Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>
    </Layout>
  );
}
