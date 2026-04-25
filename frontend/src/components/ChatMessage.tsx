import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { ChevronDown, ChevronRight, FileText, User, Bot } from 'lucide-react';
import type { Source } from '../api/chat';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

export function ChatMessage({ role, content, sources = [] }: ChatMessageProps) {
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const isUser = role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-[#29ABE2]' : 'bg-gray-200'
      }`}>
        {isUser
          ? <User size={16} className="text-white" />
          : <Bot size={16} className="text-gray-600" />
        }
      </div>
      <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'bg-[#29ABE2] text-white rounded-tr-sm'
            : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm shadow-sm'
        }`}>
          {isUser ? (
            <p>{content}</p>
          ) : (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>
          )}
        </div>
        {!isUser && sources.length > 0 && (
          <div className="w-full">
            <button
              onClick={() => setSourcesOpen(!sourcesOpen)}
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-[#29ABE2] transition-colors"
            >
              {sourcesOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
              {sources.length} source{sources.length > 1 ? 's' : ''}
            </button>
            {sourcesOpen && (
              <div className="mt-2 space-y-2">
                {sources.map((source, i) => (
                  <div key={i} className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                    <div className="flex items-center gap-1.5 mb-1">
                      <FileText size={11} className="text-gray-400" />
                      <span className="text-xs text-gray-400 font-medium">
                        Chunk {source.chunk_index + 1}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 leading-relaxed">{source.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
