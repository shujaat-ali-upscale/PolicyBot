import ReactMarkdown from 'react-markdown'
import { Bot, User, ChevronDown, ChevronUp, FileText } from 'lucide-react'
import { useState } from 'react'
import type { Source } from '../api'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  isLoading?: boolean
}

interface ChatMessageProps {
  message: Message
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const [showSources, setShowSources] = useState(false)
  const isUser = message.role === 'user'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
        ${isUser ? 'bg-violet-600' : 'bg-gray-700'}`}>
        {isUser
          ? <User className="w-4 h-4 text-white" />
          : <Bot className="w-4 h-4 text-violet-400" />}
      </div>

      {/* Bubble */}
      <div className={`max-w-[75%] flex flex-col gap-1 ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed
          ${isUser
            ? 'bg-violet-600 text-white rounded-tr-sm'
            : 'bg-gray-800 text-gray-100 rounded-tl-sm'}`}>

          {message.isLoading ? (
            <div className="flex items-center gap-1 py-1">
              <span className="typing-dot bg-gray-400" />
              <span className="typing-dot bg-gray-400" />
              <span className="typing-dot bg-gray-400" />
            </div>
          ) : (
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                code: ({ children }) => (
                  <code className="bg-black/30 rounded px-1 py-0.5 text-xs font-mono">{children}</code>
                ),
                pre: ({ children }) => (
                  <pre className="bg-black/30 rounded p-3 text-xs overflow-x-auto my-2">{children}</pre>
                ),
              }}>
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Sources accordion */}
        {message.sources && message.sources.length > 0 && (
          <div className="w-full">
            <button
              onClick={() => setShowSources((s) => !s)}
              className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-400 transition-colors">
              {showSources ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
            </button>

            {showSources && (
              <div className="mt-2 space-y-2">
                {message.sources.map((src, i) => (
                  <div key={i} className="bg-gray-900 border border-gray-700 rounded-lg p-3">
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <FileText className="w-3 h-3 text-violet-400" />
                      <span className="text-xs font-medium text-violet-400 truncate">{src.source}</span>
                    </div>
                    <p className="text-xs text-gray-500 line-clamp-3">{src.content}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
