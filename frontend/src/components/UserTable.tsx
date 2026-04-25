import { useState } from 'react';
import { Trash2, ShieldCheck, User } from 'lucide-react';
import { deleteUser } from '../api/users';
import type { User as UserType } from '../api/auth';

interface UserTableProps {
  users: UserType[];
  onUserDeleted: () => void;
}

export function UserTable({ users, onUserDeleted }: UserTableProps) {
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const handleDelete = async (user: UserType) => {
    if (!confirm(`Delete user ${user.email}? This cannot be undone.`)) return;
    setDeletingId(user.id);
    try {
      await deleteUser(user.id);
      onUserDeleted();
    } finally {
      setDeletingId(null);
    }
  };

  if (users.length === 0) {
    return <p className="text-sm text-gray-500 text-center py-8">No users found.</p>;
  }

  return (
    <div className="overflow-hidden rounded-xl border border-gray-100">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-100">
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Name</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Email</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Role</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-50 bg-white">
          {users.map((user) => (
            <tr key={user.id} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 font-medium text-gray-800">{user.name}</td>
              <td className="px-4 py-3 text-gray-600">{user.email}</td>
              <td className="px-4 py-3">
                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-semibold ${
                  user.role === 'admin'
                    ? 'bg-blue-50 text-blue-700 border border-blue-200'
                    : 'bg-gray-50 text-gray-600 border border-gray-200'
                }`}>
                  {user.role === 'admin' ? <ShieldCheck size={11} /> : <User size={11} />}
                  {user.role}
                </span>
              </td>
              <td className="px-4 py-3 text-right">
                <button
                  onClick={() => handleDelete(user)}
                  disabled={deletingId === user.id}
                  className="text-gray-400 hover:text-red-500 transition-colors disabled:opacity-40"
                  title="Delete user"
                >
                  <Trash2 size={15} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
