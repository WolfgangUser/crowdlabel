import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import {
  LayoutDashboard, ListTodo, Users, LogOut, Tag, ChevronRight
} from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { to: '/dashboard', label: 'Дашборд', icon: LayoutDashboard },
  { to: '/tasks', label: 'Задачи', icon: ListTodo },
];

export default function Layout() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const roleLabel = { admin: 'Администратор', manager: 'Менеджер', annotator: 'Аннотатор' }[user?.role ?? 'annotator'];
  const roleBadge = { admin: 'bg-rose-900/40 text-rose-300', manager: 'bg-amber-900/40 text-amber-300', annotator: 'bg-emerald-900/40 text-emerald-300' }[user?.role ?? 'annotator'];

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 font-mono">
      {/* Sidebar */}
      <aside className="w-64 flex flex-col border-r border-gray-800 bg-gray-900">
        {/* Logo */}
        <div className="px-6 py-5 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <Tag className="text-indigo-400" size={20} />
            <span className="text-lg font-bold tracking-tight text-white">CrowdLabel</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">ML Data Annotation Platform</p>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all',
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-600/30'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                )
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
          {user?.role === 'admin' && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all',
                  isActive
                    ? 'bg-rose-600/20 text-rose-300 border border-rose-600/30'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                )
              }
            >
              <Users size={16} />
              Пользователи
            </NavLink>
          )}
        </nav>

        {/* User info */}
        <div className="px-4 py-4 border-t border-gray-800">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-sm font-bold">
              {user?.username?.[0]?.toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.username}</p>
              <span className={clsx('text-xs px-1.5 py-0.5 rounded font-medium', roleBadge)}>
                {roleLabel}
              </span>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-xs text-gray-500 hover:text-red-400 transition-colors w-full"
          >
            <LogOut size={14} />
            Выйти
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
