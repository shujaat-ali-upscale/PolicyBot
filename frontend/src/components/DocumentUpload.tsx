import { useState, useCallback } from 'react';
import { Upload, Trash2, CheckCircle, AlertCircle } from 'lucide-react';
import { uploadDocument, deleteDocument } from '../api/documents';
import type { DocumentStatus } from '../api/documents';

interface DocumentUploadProps {
  status: DocumentStatus | null;
  onStatusChange: () => void;
}

export function DocumentUpload({ status, onStatusChange }: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [uploadResult, setUploadResult] = useState<{ success: boolean; message: string } | null>(null);

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadResult({ success: false, message: 'Only PDF files are supported.' });
      return;
    }
    setIsUploading(true);
    setUploadResult(null);
    try {
      const res = await uploadDocument(file);
      setUploadResult({
        success: true,
        message: `Uploaded successfully — ${res.data.chunks_created} chunks created.`,
      });
      onStatusChange();
    } catch {
      setUploadResult({ success: false, message: 'Upload failed. Please try again.' });
    } finally {
      setIsUploading(false);
    }
  }, [onStatusChange]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleDelete = async () => {
    if (!confirm('Delete the policy document? Employees will not be able to get answers until a new document is uploaded.')) return;
    setIsDeleting(true);
    try {
      await deleteDocument();
      onStatusChange();
      setUploadResult(null);
    } catch {
      setUploadResult({ success: false, message: 'Delete failed. Please try again.' });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-4">
      {status?.has_document && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CheckCircle size={18} className="text-emerald-600 flex-shrink-0" />
            <div>
              <p className="text-sm font-semibold text-emerald-800">{status.filename}</p>
              <p className="text-xs text-emerald-600">{status.chunk_count} chunks indexed</p>
            </div>
          </div>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="flex items-center gap-1.5 text-sm text-red-500 hover:text-red-700 transition-colors disabled:opacity-50"
          >
            <Trash2 size={14} />
            {isDeleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      )}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors ${
          isDragging
            ? 'border-[#29ABE2] bg-blue-50'
            : 'border-gray-300 hover:border-[#29ABE2] bg-white'
        }`}
      >
        <Upload size={32} className="text-gray-400 mx-auto mb-3" />
        <p className="text-sm font-medium text-gray-700 mb-1">Drag & drop your policy PDF here</p>
        <p className="text-xs text-gray-400 mb-4">or click to browse</p>
        <label className="cursor-pointer">
          <span className="px-4 py-2 bg-[#29ABE2] hover:bg-[#2196cc] text-white text-sm rounded-lg transition-colors">
            {isUploading ? 'Uploading...' : 'Choose File'}
          </span>
          <input
            type="file"
            accept=".pdf"
            className="hidden"
            disabled={isUploading}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
              e.target.value = '';
            }}
          />
        </label>
      </div>
      {uploadResult && (
        <div className={`flex items-center gap-2 p-3 rounded-lg border text-sm ${
          uploadResult.success
            ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
            : 'bg-red-50 border-red-200 text-red-700'
        }`}>
          {uploadResult.success
            ? <CheckCircle size={15} className="flex-shrink-0" />
            : <AlertCircle size={15} className="flex-shrink-0" />
          }
          {uploadResult.message}
        </div>
      )}
    </div>
  );
}
