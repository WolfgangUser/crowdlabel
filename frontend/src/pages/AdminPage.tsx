import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usersApi } from '../api/client';
import { useAuthStore } from '../store/authStore';
import { Shield, UserX } from 'lucide-react';
import type { User, UserRole } from '../types';

const ROLES: UserRole[] = ['admin', 'manager', 'annotator'];
const roleBadge: Record<UserRole, string> = {
  admin: 'bg-rose-900/40 text-rose-300',
  manager: 'bg-amber-900/40 text-amber-300',
  annotator: 'bg-emerald-900/40 text-emerald-300',
};

export default function AdminPage() {
  const currentUser = useAuthStore((s) => s.user);
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => usersApi.list({ size: 100 }).then((r) => r.data),
  });

  const updateRoleMutation = useMutation({
    mutationFn: ({ id, role }: { id: number; role: string }) => usersApi.updateRole(id, role),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: number) => usersApi.deactivate(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  });

  const users: User[] = data?.items ?? [];

  return (
    <div className="p-8 font-mono">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Shield size={24} className="text-rose-400" />
          Управление пользователями
        </h1>
        <p className="text-gray-400 text-sm mt-1">{data?.total ?? 0} пользователей в системе</p>
      </div>

      {isLoading ? (
        <div className="text-gray-400">Загрузка...</div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-left">
                <th className="px-5 py-3 text-xs text-gray-500 uppercase tracking-wider">Пользователь</th>
                <th className="px-5 py-3 text-xs text-gray-500 uppercase tracking-wider">Email</th>
                <th className="px-5 py-3 text-xs text-gray-500 uppercase tracking-wider">Роль</th>
                <th className="px-5 py-3 text-xs text-gray-500 uppercase tracking-wider">Статус</th>
                <th className="px-5 py-3 text-xs text-gray-500 uppercase tracking-wider">Действия</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-indigo-700 flex items-center justify-center text-xs font-bold text-white">
                        {user.username[0].toUpperCase()}
                      </div>
                      <div>
                        <p className="text-white font-medium">{user.username}</p>
                        {user.full_name && <p className="text-gray-500 text-xs">{user.full_name}</p>}
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-3 text-gray-400">{user.email}</td>
                  <td className="px-5 py-3">
                    {user.id === currentUser?.id ? (
                      <span className={`text-xs px-2 py-0.5 rounded font-medium ${roleBadge[user.role]}`}>
                        {user.role} (вы)
                      </span>
                    ) : (
                      <select
                        value={user.role}
                        onChange={(e) => updateRoleMutation.mutate({ id: user.id, role: e.target.value })}
                        className="text-xs bg-gray-800 border border-gray-700 text-white rounded px-2 py-1 focus:outline-none focus:border-indigo-500"
                      >
                        {ROLES.map((r) => (
                          <option key={r} value={r}>{r}</option>
                        ))}
                      </select>
                    )}
                  </td>
                  <td className="px-5 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      user.is_active ? 'bg-emerald-900/40 text-emerald-400' : 'bg-gray-800 text-gray-500'
                    }`}>
                      {user.is_active ? 'активен' : 'деактивирован'}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    {user.id !== currentUser?.id && user.is_active && (
                      <button
                        onClick={() => {
                          if (confirm(`Деактивировать ${user.username}?`)) {
                            deactivateMutation.mutate(user.id);
                          }
                        }}
                        className="flex items-center gap-1 text-xs text-red-400 hover:text-red-300 transition"
                      >
                        <UserX size={14} />
                        Деактивировать
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
