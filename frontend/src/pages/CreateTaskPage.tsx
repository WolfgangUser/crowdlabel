import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { tasksApi } from '../api/client';
import { ArrowLeft, Plus } from 'lucide-react';

// Inline datasets API since we may not have a datasets endpoint yet
import { api } from '../api/client';

export default function CreateTaskPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    title: '',
    description: '',
    dataset_id: '',
    text: '',
    url: '',
    annotations_required: 3,
    reward_points: 10,
    task_type: 'text',
  });
  const [error, setError] = useState('');

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => api.get('/datasets').then(r => r.data?.items ?? []).catch(() => []),
  });

  const mutation = useMutation({
    mutationFn: () => {
      const data: Record<string, unknown> = {
        title: form.title,
        description: form.description || undefined,
        dataset_id: parseInt(form.dataset_id),
        annotations_required: form.annotations_required,
        reward_points: form.reward_points,
        data: form.task_type === 'text'
          ? { text: form.text }
          : { url: form.url },
      };
      return tasksApi.create(data);
    },
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      navigate(`/tasks/${res.data.id}`);
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail.map((d: any) => d.msg).join(', ') : (detail ?? 'Ошибка создания'));
    },
  });

  const set = (k: keyof typeof form) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) return setError('Введите название задачи');
    if (!form.dataset_id) return setError('Выберите датасет');
    if (form.task_type === 'text' && !form.text.trim()) return setError('Введите текст для разметки');
    if (form.task_type === 'image' && !form.url.trim()) return setError('Введите URL изображения');
    setError('');
    mutation.mutate();
  };

  const inputClass = "w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition";
  const labelClass = "block text-xs text-gray-400 mb-1.5 uppercase tracking-wider";

  return (
    <div className="p-8 font-mono max-w-2xl">
      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-gray-500 hover:text-gray-300 text-sm mb-6 transition">
        <ArrowLeft size={16} /> Назад
      </button>

      <h1 className="text-2xl font-bold text-white mb-6">Создать задачу разметки</h1>

      {error && (
        <div className="bg-red-950/50 border border-red-800 text-red-300 text-sm rounded-lg px-4 py-3 mb-6">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className={labelClass}>Название задачи *</label>
          <input type="text" value={form.title} onChange={set('title')} required
            placeholder="Например: Классификация изображений #001"
            className={inputClass} />
        </div>

        <div>
          <label className={labelClass}>Описание</label>
          <textarea value={form.description} onChange={set('description')}
            placeholder="Инструкции для аннотаторов..."
            rows={3} className={inputClass + " resize-none"} />
        </div>

        <div>
          <label className={labelClass}>Датасет *</label>
          <select value={form.dataset_id} onChange={set('dataset_id')} className={inputClass}>
            <option value="">— Выберите датасет —</option>
            {(datasets ?? []).map((ds: any) => (
              <option key={ds.id} value={ds.id}>{ds.name}</option>
            ))}
            {(!datasets || datasets.length === 0) && (
              <option value="1">Датасет #1 (по умолчанию)</option>
            )}
          </select>
          {(!datasets || datasets.length === 0) && (
            <p className="text-xs text-amber-400 mt-1">
              Введите ID датасета вручную — датасеты созданы через seed.py (id: 1, 2, 3)
            </p>
          )}
        </div>

        {(!datasets || datasets.length === 0) && (
          <div>
            <label className={labelClass}>ID датасета *</label>
            <input type="number" value={form.dataset_id} onChange={set('dataset_id')}
              placeholder="1" min="1" className={inputClass} />
          </div>
        )}

        <div>
          <label className={labelClass}>Тип данных</label>
          <div className="flex gap-3">
            {[['text', 'Текст'], ['image', 'Изображение']].map(([val, label]) => (
              <button key={val} type="button"
                onClick={() => setForm(f => ({ ...f, task_type: val }))}
                className={`px-4 py-2 rounded-lg text-sm transition ${form.task_type === val ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'}`}>
                {label}
              </button>
            ))}
          </div>
        </div>

        {form.task_type === 'text' ? (
          <div>
            <label className={labelClass}>Текст для разметки *</label>
            <textarea value={form.text} onChange={set('text')}
              placeholder="Вставьте текст, который нужно размечать..."
              rows={4} className={inputClass + " resize-none"} />
          </div>
        ) : (
          <div>
            <label className={labelClass}>URL изображения *</label>
            <input type="url" value={form.url} onChange={set('url')}
              placeholder="https://example.com/image.jpg"
              className={inputClass} />
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Кол-во аннотаций</label>
            <input type="number" min="1" max="10"
              value={form.annotations_required}
              onChange={e => setForm(f => ({ ...f, annotations_required: parseInt(e.target.value) }))}
              className={inputClass} />
            <p className="text-xs text-gray-500 mt-1">Сколько аннотаторов должны разметить задачу (1–10)</p>
          </div>
          <div>
            <label className={labelClass}>Вознаграждение (очков)</label>
            <input type="number" min="1" max="1000"
              value={form.reward_points}
              onChange={e => setForm(f => ({ ...f, reward_points: parseInt(e.target.value) }))}
              className={inputClass} />
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button type="submit" disabled={mutation.isPending}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium py-2.5 px-6 rounded-lg text-sm transition">
            <Plus size={16} />
            {mutation.isPending ? 'Создание...' : 'Создать задачу'}
          </button>
          <button type="button" onClick={() => navigate(-1)}
            className="bg-gray-800 hover:bg-gray-700 text-gray-300 font-medium py-2.5 px-6 rounded-lg text-sm transition">
            Отмена
          </button>
        </div>
      </form>
    </div>
  );
}
