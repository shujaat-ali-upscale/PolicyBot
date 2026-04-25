import { useState, useRef } from 'react'
import { Upload, FileText, Trash2, CheckCircle, AlertCircle, Loader2, X } from 'lucide-react'
import { uploadDocument, listDocuments, clearDocuments } from '../api'

interface DocumentPanelProps {
  onDocumentsChange: () => void
  documents: string[]
}

export default function DocumentPanel({ onDocumentsChange, documents }: DocumentPanelProps) {
  const [uploading, setUploading] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const notify = (type: 'success' | 'error', msg: string) => {
    setNotification({ type, msg })
    setTimeout(() => setNotification(null), 4000)
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const res = await uploadDocument(file)
      notify('success', `✓ ${res.filename} — ${res.chunks_added} chunks indexed`)
      onDocumentsChange()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Upload failed'
      notify('error', msg)
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const handleClear = async () => {
    if (!confirm('Delete ALL indexed documents? This cannot be undone.')) return
    setClearing(true)
    try {
      await clearDocuments()
      notify('success', 'All documents cleared.')
      onDocumentsChange()
    } catch {
      notify('error', 'Failed to clear documents.')
    } finally {
      setClearing(false)
    }
  }

  return (
    <aside className="w-72 bg-gray-900 border-r border-gray-800 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Knowledge Base</h2>
        <p className="text-xs text-gray-500 mt-1">Upload docs to chat with</p>
      </div>

      {/* Upload button */}
      <div className="p-4 border-b border-gray-800">
        <label className={`flex items-center justify-center gap-2 w-full py-2.5 px-4 rounded-lg cursor-pointer text-sm font-medium transition-all
          ${uploading
            ? 'bg-violet-800 text-violet-300 cursor-not-allowed'
            : 'bg-violet-600 hover:bg-violet-500 text-white'}`}>
          {uploading ? (
            <><Loader2 className="w-4 h-4 animate-spin" /> Uploading…</>
          ) : (
            <><Upload className="w-4 h-4" /> Upload Document</>
          )}
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.txt,.md"
            className="hidden"
            onChange={handleUpload}
            disabled={uploading}
          />
        </label>
        <p className="text-xs text-gray-600 mt-2 text-center">PDF · TXT · Markdown</p>
      </div>

      {/* Document list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {documents.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="w-10 h-10 text-gray-700 mx-auto mb-2" />
            <p className="text-xs text-gray-600">No documents yet</p>
          </div>
        ) : (
          documents.map((doc) => (
            <div key={doc} className="flex items-center gap-2 bg-gray-800 rounded-lg px-3 py-2">
              <FileText className="w-4 h-4 text-violet-400 flex-shrink-0" />
              <span className="text-xs text-gray-300 truncate flex-1" title={doc}>{doc}</span>
            </div>
          ))
        )}
      </div>

      {/* Clear button */}
      {documents.length > 0 && (
        <div className="p-4 border-t border-gray-800">
          <button
            onClick={handleClear}
            disabled={clearing}
            className="flex items-center justify-center gap-2 w-full py-2 px-4 rounded-lg text-sm text-red-400 hover:text-red-300 hover:bg-red-900/30 transition-all disabled:opacity-50">
            {clearing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
            Clear All Documents
          </button>
        </div>
      )}

      {/* Notification toast */}
      {notification && (
        <div className={`absolute bottom-4 left-4 right-4 flex items-start gap-2 p-3 rounded-lg text-xs shadow-lg z-50
          ${notification.type === 'success' ? 'bg-emerald-900 text-emerald-200' : 'bg-red-900 text-red-200'}`}>
          {notification.type === 'success'
            ? <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            : <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />}
          <span className="flex-1">{notification.msg}</span>
          <button onClick={() => setNotification(null)}><X className="w-3 h-3" /></button>
        </div>
      )}
    </aside>
  )
}
