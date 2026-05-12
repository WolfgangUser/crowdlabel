import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '../store/authStore';
import { tasksApi, annotationsApi } from '../api/client';
import { CheckCircle, Clock, ListTodo, Star, TrendingUp } from 'lucide-react';
import type { Task, Annotation } from '../types';

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);

  const { data: tasksData } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasksApi.list({ size: 100 }).then((r) => r.data),
  });

  const { data: myAnnotations } = useQuery({
    queryKey: ['my-annotations'],
    queryFn: () => annotationsApi.myAnnotations().then((r) => r.data as Annotation[]),
  });

  const tasks: Task[] = tasksData?.items ?? [];
  const activeTasks = tasks.filter((t) => t.status === 'active').length;
  const completedTasks = tasks.filter((t) => t.status === 'completed').length;
  const myTotal = myAnnotations?.length ?? 0;
  const myVerified = myAnnotations?.filter((a) => a.status === 'verified').length ?? 0;

  const stats = [
    { label: 'Активные задачи', value: activeTasks, icon: Clock, color: 'text-amber-400', bg: 'bg-amber-900/20 border-amber-800/30' },
    { label: 'Завершённые задачи', value: completedTasks, icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-900/20 border-emerald-800/30' },
    { label: 'Моих аннотаций', value: myTotal, icon: ListTodo, color: 'text-indigo-400', bg: 'bg-indigo-900/20 border-indigo-800/30' },
    { label: 'Подтверждено', value: myVerified, icon: Star, color: 'text-rose-400', bg: 'bg-rose-900/20 border-rose-800/30' },
  ];

  const roleLabel = { admin: 'Администратор', manager: 'Менеджер', annotator: 'Аннотатор' }[user?.role ?? 'annotator'];

  return (
    <div className="p-8 font-mono">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">
          Привет, {user?.full_name ?? user?.username} 👋
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Роль: <span className="text-indigo-400">{roleLabel}</span> · {user?.email}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className={`border rounded-xl p-5 ${bg}`}>
            <div className="flex items-center justify-between mb-3">
              <Icon size={18} className={color} />
              <span className={`text-2xl font-bold ${color}`}>{value}</span>
            </div>
            <p className="text-xs text-gray-400">{label}</p>
          </div>
        ))}
      </div>

      {/* Recent tasks */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-5">
          <TrendingUp size={16} className="text-indigo-400" />
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">Последние задачи</h2>
        </div>
        <div className="space-y-2">
          {tasks.slice(0, 5).map((task) => (
            <div key={task.id} className="flex items-center justify-between py-2.5 border-b border-gray-800 last:border-0">
              <div>
                <p className="text-sm text-white">{task.title}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {task.annotation_count}/{task.annotations_required} аннотаций
                </p>
              </div>
              <span className={`text-xs px-2 py-1 rounded font-medium ${
                task.status === 'active' ? 'bg-emerald-900/40 text-emerald-400' :
                task.status === 'completed' ? 'bg-blue-900/40 text-blue-400' :
                task.status === 'draft' ? 'bg-gray-800 text-gray-400' :
                'bg-gray-800 text-gray-400'
              }`}>
                {task.status}
              </span>
            </div>
          ))}
          {tasks.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-4">Нет задач</p>
          )}
        </div>
      </div>
    </div>
  );
}
