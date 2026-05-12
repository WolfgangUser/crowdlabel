import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { tasksApi } from '../api/client';
import { useAuthStore } from '../store/authStore';
import { ChevronRight, Filter, Plus } from 'lucide-react';
import type { Task, TaskStatus } from '../types';

const STATUS_OPTS: { value: TaskStatus | ''; label: string }[] = [
  { value: '', label: 'Все' },
  { value: 'active', label: 'Активные' },
  { value: 'draft', label: 'Черновики' },
  { value: 'completed', label: 'Завершённые' },
  { value: 'archived', label: 'Архив' },
];

const statusStyle: Record<TaskStatus, string> = {
  active: 'bg-emerald-900/40 text-emerald-400',
  completed: 'bg-blue-900/40 text-blue-400',
  draft: 'bg-gray-800 text-gray-400',
  archived: 'bg-gray-900 text-gray-600',
};

export default function TasksPage() {
  const user = useAuthStore((s) => s.user);
  const [status, setStatus] = useState<TaskStatus | ''>('');
  const [page, setPage] = useState(1);

  const endpoint = user?.role === 'annotator' ? tasksApi.available : tasksApi.list;

  const { data, isLoading } = useQuery({
    queryKey: ['tasks', status, page, user?.role],
    queryFn: () => endpoint({ status: status || undefined, page, size: 20 }).then((r) => r.data),
  });

  const tasks: Task[] = data?.items ?? [];
  const totalPages = data?.pages ?? 1;

  return (
    <div className="p-8 font-mono">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Задачи разметки</h1>
          <p className="text-gray-400 text-sm mt-1">
            {data?.total ?? 0} задач
            {user?.role === 'annotator' && ' · доступных для разметки'}
          </p>
        </div>
        {(user?.role === 'manager' || user?.role === 'admin') && (
          <Link
            to="/tasks/new"
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-4 py-2 rounded-lg transition"
          >
            <Plus size={16} />
            Создать задачу
          </Link>
        )}
      </div>

      {/* Filters */}
      {user?.role !== 'annotator' && (
        <div className="flex items-center gap-2 mb-5">
          <Filter size={14} className="text-gray-500" />
          {STATUS_OPTS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => { setStatus(value as TaskStatus | ''); setPage(1); }}
              className={`text-xs px-3 py-1.5 rounded-lg transition ${
                status === value
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      )}

      {/* Tasks list */}
      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Загрузка...</div>
      ) : tasks.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-400">Задачи не найдены</p>
          {user?.role === 'annotator' && (
            <p className="text-gray-600 text-sm mt-2">Все доступные задачи уже размечены</p>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          {tasks.map((task) => (
            <Link
              key={task.id}
              to={`/tasks/${task.id}`}
              className="flex items-center justify-between bg-gray-900 border border-gray-800 hover:border-indigo-600/50 rounded-xl px-5 py-4 transition group"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="text-sm font-medium text-white group-hover:text-indigo-300 transition truncate">
                    {task.title}
                  </h3>
                  <span className={`text-xs px-2 py-0.5 rounded font-medium flex-shrink-0 ${statusStyle[task.status]}`}>
                    {task.status}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span>{task.annotation_count}/{task.annotations_required} аннотаций</span>
                  <span>{task.reward_points} очков</span>
                  <span>{new Date(task.created_at).toLocaleDateString('ru')}</span>
                </div>
              </div>
              <ChevronRight size={16} className="text-gray-600 group-hover:text-indigo-400 transition flex-shrink-0 ml-4" />
            </Link>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-6">
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
            <button
              key={p}
              onClick={() => setPage(p)}
              className={`w-8 h-8 rounded text-sm transition ${
                page === p ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
