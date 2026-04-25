import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2 min — LLM can be slow on first run
})

// ── Types ──────────────────────────────────────────────────────────────────────

export interface Source {
  source: string
  content: string
}

export interface ChatResponse {
  answer: string
  sources: Source[]
}

export interface UploadResponse {
  filename: string
  chunks_added: number
  message: string
}

export interface DocumentListResponse {
  sources: string[]
  total: number
}

export interface HealthResponse {
  status: string
  llm_provider: string
  model: string
  embedding_model: string
}

// ── API Calls ──────────────────────────────────────────────────────────────────

export const sendMessage = async (question: string, k = 4): Promise<ChatResponse> => {
  const { data } = await api.post<ChatResponse>('/chat', { question, k })
  return data
}

export const uploadDocument = async (file: File): Promise<UploadResponse> => {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<UploadResponse>('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export const listDocuments = async (): Promise<DocumentListResponse> => {
  const { data } = await api.get<DocumentListResponse>('/documents')
  return data
}

export const clearDocuments = async (): Promise<{ message: string }> => {
  const { data } = await api.delete('/documents')
  return data
}

export const checkHealth = async (): Promise<HealthResponse> => {
  const { data } = await api.get<HealthResponse>('/health')
  return data
}
