import { useState, useEffect, useCallback } from 'react';
import { Upload, Users, Loader2, AlertCircle } from 'lucide-react';
import { getDocumentStatus } from '../api/documents';
import { listUsers } from '../api/users';
import { DocumentUpload } from '../components/DocumentUpload';
import { UserTable } from '../components/UserTable';
import { Layout } from '../components/Layout';
import type { DocumentStatus } from '../api/documents';
import type { User } from '../api/auth';

type Tab = 'upload' | 'users';

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState<Tab>('upload');
  const [docStatus, setDocStatus] = useState<DocumentStatus | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [statusRes, usersRes] = await Promise.all([
        getDocumentStatus(),
        listUsers(),
      ]);
      setDocStatus(statusRes.data);
      setUsers(usersRes.data.users);
    } catch {
      setError('Failed to load data. Please refresh.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'upload', label: 'Policy Document', icon: <Upload size={15} /> },
    { id: 'users', label: `Users (${users.length})`, icon: <Users size={15} /> },
  ];

  return (
    <Layout>
      <div className="max-w-3xl mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
          <p className="text-gray-500 text-sm mt-1">Manage the policy document and user accounts</p>
        </div>
        {error && (
          <div className="mb-6 p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2">
            <AlertCircle size={16} className="text-red-600 flex-shrink-0" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
        <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-xl w-fit">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-white text-[#29ABE2] shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Loader2 size={24} className="text-[#29ABE2] animate-spin" />
          </div>
        ) : (
          <>
            {activeTab === 'upload' && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <h2 className="text-base font-semibold text-gray-800 mb-2">Upload Policy Document</h2>
                <p className="text-sm text-gray-500 mb-5">
                  Upload a PDF of your company policy. Employees can ask questions about it in the chat.
                  Uploading a new document replaces the current one.
                </p>
                <DocumentUpload status={docStatus} onStatusChange={fetchData} />
              </div>
            )}
            {activeTab === 'users' && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <h2 className="text-base font-semibold text-gray-800 mb-4">User Accounts</h2>
                <UserTable users={users} onUserDeleted={fetchData} />
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}
