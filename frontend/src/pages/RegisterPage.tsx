import { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Tag, AlertCircle, CheckCircle } from 'lucide-react';
import { authApi } from '../api/client';

export default function RegisterPage() {
  const [form, setForm] = useState({ email: '', username: '', password: '', full_name: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await authApi.register(form);
      setSuccess(true);
      setTimeout(() => navigate('/login'), 2000);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail.map((d: any) => d.msg).join(', ') : (detail ?? 'Ошибка регистрации'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4 font-mono">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(99,102,241,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(99,102,241,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />

      <div className="relative w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center">
              <Tag size={20} className="text-white" />
            </div>
            <span className="text-2xl font-bold text-white">CrowdLabel</span>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">
          <h1 className="text-xl font-bold text-white mb-6">Регистрация</h1>

          {success && (
            <div className="flex items-center gap-2 bg-green-950/50 border border-green-800 text-green-300 text-sm rounded-lg px-4 py-3 mb-6">
              <CheckCircle size={16} />
              Аккаунт создан! Перенаправление...
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 bg-red-950/50 border border-red-800 text-red-300 text-sm rounded-lg px-4 py-3 mb-6">
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {([
              ['email', 'Email', 'email', 'user@example.com'],
              ['username', 'Имя пользователя', 'text', 'username123'],
              ['full_name', 'Полное имя (опционально)', 'text', 'Иванов Иван'],
              ['password', 'Пароль', 'password', 'Min 8 символов, 1 заглавная, 1 цифра'],
            ] as const).map(([key, label, type, placeholder]) => (
              <div key={key}>
                <label className="block text-xs text-gray-400 mb-1.5 uppercase tracking-wider">{label}</label>
                <input
                  type={type}
                  value={form[key as keyof typeof form]}
                  onChange={set(key as keyof typeof form)}
                  required={key !== 'full_name'}
                  placeholder={placeholder}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                />
              </div>
            ))}

            <button
              type="submit"
              disabled={loading || success}
              className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium py-2.5 px-4 rounded-lg text-sm transition mt-2"
            >
              {loading ? 'Регистрация...' : 'Создать аккаунт'}
            </button>
          </form>

          <p className="text-center text-xs text-gray-500 mt-4">
            Уже есть аккаунт?{' '}
            <Link to="/login" className="text-indigo-400 hover:text-indigo-300">Войти</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
