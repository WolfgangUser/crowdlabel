import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tasksApi, annotationsApi } from '../api/client';
import { useAuthStore } from '../store/authStore';
import { CheckCircle, XCircle, AlertCircle, ArrowLeft } from 'lucide-react';
import type { Task, Annotation } from '../types';

export default function TaskDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const qc = useQueryClient();
  const [selectedLabel, setSelectedLabel] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const taskId = parseInt(id ?? '0');

  const { data: task, isLoading } = useQuery<Task>({
    queryKey: ['task', taskId],
    queryFn: () => tasksApi.get(taskId).then((r) => r.data),
    enabled: !!taskId,
  });

  const { data: annotations } = useQuery<Annotation[]>({
    queryKey: ['annotations', taskId],
    queryFn: () => annotationsApi.forTask(taskId).then((r) => r.data),
    enabled: !!taskId && user?.role !== 'annotator',
  });

  const submitMutation = useMutation({
    mutationFn: () => annotationsApi.submit({ task_id: taskId, label: selectedLabel }),
    onSuccess: () => {
      setSuccess('Аннотация отправлена!');
      setSelectedLabel('');
      qc.invalidateQueries({ queryKey: ['task', taskId] });
      qc.invalidateQueries({ queryKey: ['tasks'] });
      qc.invalidateQueries({ queryKey: ['my-annotations'] });
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail ?? 'Ошибка отправки');
    },
  });

  const verifyMutation = useMutation({
    mutationFn: ({ aid, status }: { aid: number; status: string }) =>
      annotationsApi.verify(aid, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['annotations', taskId] });
      qc.invalidateQueries({ queryKey: ['my-annotations'] });
    },
  });

  if (isLoading) return <div className="p-8 text-gray-400 font-mono">Загрузка...</div>;
  if (!task) return <div className="p-8 text-red-400 font-mono">Задача не найдена</div>;

  // Assume labels are stored in task data or fetch from dataset
  const labels = (task.data as any).labels ?? ['positive', 'negative', 'neutral', 'cat', 'dog'];

  return (
    <div className="p-8 font-mono max-w-3xl">
      {/* Back */}
      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-gray-500 hover:text-gray-300 text-sm mb-6 transition">
        <ArrowLeft size={16} />
        Назад
      </button>

      {/* Task header */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <h1 className="text-xl font-bold text-white">{task.title}</h1>
          <span className={`text-xs px-2 py-1 rounded font-medium ${
            task.status === 'active' ? 'bg-emerald-900/40 text-emerald-400' :
            task.status === 'completed' ? 'bg-blue-900/40 text-blue-400' :
            'bg-gray-800 text-gray-400'
          }`}>
            {task.status}
          </span>
        </div>

        {task.description && <p className="text-gray-400 text-sm mb-4">{task.description}</p>}

        {/* Task data */}
        <div className="bg-gray-800/50 rounded-lg p-4 mb-4">
          {(task.data as any).text && (
            <p className="text-gray-200 text-sm leading-relaxed">"{(task.data as any).text}"</p>
          )}
          {(task.data as any).url && (
            <img
              src={(task.data as any).url}
              alt="Задача"
              className="max-h-64 object-contain rounded"
              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
            />
          )}
          {(task.data as any).tokens && (
            <div className="flex flex-wrap gap-2">
              {(task.data as any).tokens.map((t: string, i: number) => (
                <span key={i} className="bg-indigo-900/40 border border-indigo-800/50 text-indigo-300 px-2 py-1 rounded text-sm">{t}</span>
              ))}
            </div>
          )}
        </div>

        <div className="flex gap-4 text-xs text-gray-500">
          <span>Аннотаций: {task.annotation_count}/{task.annotations_required}</span>
          <span>Вознаграждение: {task.reward_points} очков</span>
        </div>
      </div>

      {/* Annotation form (annotators) */}
      {task.status === 'active' && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-4">Выберите метку</h2>

          {error && (
            <div className="flex items-center gap-2 bg-red-950/50 border border-red-800 text-red-300 text-sm rounded-lg px-4 py-2 mb-4">
              <AlertCircle size={14} />
              {error}
            </div>
          )}
          {success && (
            <div className="flex items-center gap-2 bg-green-950/50 border border-green-800 text-green-300 text-sm rounded-lg px-4 py-2 mb-4">
              <CheckCircle size={14} />
              {success}
            </div>
          )}

          <div className="flex flex-wrap gap-2 mb-4">
            {labels.map((label: string) => (
              <button
                key={label}
                onClick={() => setSelectedLabel(label)}
                className={`px-4 py-2 rounded-lg text-sm transition ${
                  selectedLabel === label
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <button
            onClick={() => submitMutation.mutate()}
            disabled={!selectedLabel || submitMutation.isPending}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm px-6 py-2 rounded-lg transition"
          >
            {submitMutation.isPending ? 'Отправка...' : 'Отправить аннотацию'}
          </button>
        </div>
      )}

      {/* Annotations list (managers/admins) */}
      {annotations && annotations.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-4">
            Аннотации ({annotations.length})
          </h2>
          <div className="space-y-3">
            {annotations.map((ann) => (
              <div key={ann.id} className="flex items-center justify-between bg-gray-800/50 rounded-lg px-4 py-3">
                <div>
                  <span className="text-sm text-white font-medium">{ann.label}</span>
                  <span className="text-xs text-gray-500 ml-3">user #{ann.annotator_id}</span>
                  {ann.comment && <p className="text-xs text-gray-500 mt-1">{ann.comment}</p>}
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    ann.status === 'verified' ? 'bg-emerald-900/40 text-emerald-400' :
                    ann.status === 'rejected' ? 'bg-red-900/40 text-red-400' :
                    'bg-gray-700 text-gray-400'
                  }`}>
                    {ann.status}
                  </span>
                  {ann.status === 'pending' && user?.role !== 'annotator' && (
                    <div className="flex gap-1">
                      <button
                        onClick={() => verifyMutation.mutate({ aid: ann.id, status: 'verified' })}
                        className="p-1.5 bg-emerald-900/40 hover:bg-emerald-900/70 text-emerald-400 rounded transition"
                        title="Подтвердить"
                      >
                        <CheckCircle size={14} />
                      </button>
                      <button
                        onClick={() => verifyMutation.mutate({ aid: ann.id, status: 'rejected' })}
                        className="p-1.5 bg-red-900/40 hover:bg-red-900/70 text-red-400 rounded transition"
                        title="Отклонить"
                      >
                        <XCircle size={14} />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
