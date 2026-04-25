import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Loader2, BotMessageSquare } from 'lucide-react'
import ChatMessage from './components/ChatMessage'
import DocumentPanel from './components/DocumentPanel'
import { sendMessage, listDocuments, checkHealth } from './api'
import type { Message } from './components/ChatMessage'
import type { HealthResponse } from './api'

const WELCOME: Message = {
  id: 'welcome',
  role: 'assistant',
  content: `👋 **Welcome to RAG Chatbot!**

Upload a document on the left (PDF, TXT, or Markdown), then ask me anything about it.

**How it works:**
1. Your document is split into chunks and embedded with a local ML model
2. When you ask a question, the most relevant chunks are retrieved from the vector database
3. Those chunks are sent to the LLM as context to generate a grounded answer

_Upload a document to get started!_`,
}

let msgIdCounter = 0
const uid = () => `msg-${++msgIdCounter}-${Date.now()}`

export default function App() {
  const [messages, setMessages] = useState<Message[]>([WELCOME])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [documents, setDocuments] = useState<string[]>([])
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Fetch health + documents on mount
  useEffect(() => {
    refreshDocuments()
    checkHealth()
      .then(setHealth)
      .catch(() => null)
  }, [])

  const refreshDocuments = useCallback(async () => {
    try {
      const res = await listDocuments()
      setDocuments(res.sources)
    } catch {
      setDocuments([])
    }
  }, [])

  const handleSend = async () => {
    const question = input.trim()
    if (!question || loading) return

    const userMsg: Message = { id: uid(), role: 'user', content: question }
    const loadingMsg: Message = { id: uid(), role: 'assistant', content: '', isLoading: true }

    setMessages((prev) => [...prev, userMsg, loadingMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await sendMessage(question)
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingMsg.id
            ? { ...m, content: res.answer, sources: res.sources, isLoading: false }
            : m
        )
      )
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      const errMsg = detail ?? 'Something went wrong. Is the backend running?'
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingMsg.id
            ? { ...m, content: `❌ Error: ${errMsg}`, isLoading: false }
            : m
        )
      )
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Auto-resize textarea
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    const ta = e.target
    ta.style.height = 'auto'
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950">
      {/* Sidebar */}
      <DocumentPanel documents={documents} onDocumentsChange={refreshDocuments} />

      {/* Main chat */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Top bar */}
        <header className="flex items-center justify-between px-6 py-4 border-b border-gray-800 bg-gray-900">
          <div className="flex items-center gap-3">
            <BotMessageSquare className="w-6 h-6 text-violet-400" />
            <div>
              <h1 className="text-sm font-semibold text-white">RAG Chatbot</h1>
              <p className="text-xs text-gray-500">LangChain · ChromaDB · Ollama</p>
            </div>
          </div>
          {health && (
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-gray-400">
                {health.llm_provider === 'ollama' ? '🦙' : '🤗'} {health.model}
              </span>
            </div>
          )}
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input area */}
        <div className="p-4 border-t border-gray-800 bg-gray-900">
          {documents.length === 0 && (
            <p className="text-xs text-amber-500 text-center mb-2">
              ⚠ Upload a document first to get accurate, grounded answers
            </p>
          )}
          <div className="flex items-end gap-3 bg-gray-800 rounded-2xl px-4 py-3">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents…"
              rows={1}
              className="flex-1 bg-transparent text-sm text-gray-100 placeholder-gray-500 resize-none outline-none leading-relaxed"
              style={{ minHeight: '24px', maxHeight: '160px' }}
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="flex-shrink-0 w-9 h-9 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-all">
              {loading
                ? <Loader2 className="w-4 h-4 text-white animate-spin" />
                : <Send className="w-4 h-4 text-white" />}
            </button>
          </div>
          <p className="text-xs text-gray-700 text-center mt-2">Enter to send · Shift+Enter for newline</p>
        </div>
      </div>
    </div>
  )
}
