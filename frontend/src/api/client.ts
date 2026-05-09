import axios, { AxiosError } from 'axios';
import type { TokenResponse } from '../types';

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
});

// ─── Request interceptor: добавляем JWT ──────────────────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── Response interceptor: обновление токена при 401 ─────────────────────────
let refreshing = false;
let queue: Array<(token: string) => void> = [];

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as typeof error.config & { _retry?: boolean };

    if (error.response?.status === 401 && !original._retry && original.url !== '/auth/refresh') {
      if (refreshing) {
        return new Promise((resolve) => {
          queue.push((token) => {
            original.headers!.Authorization = `Bearer ${token}`;
            resolve(api(original));
          });
        });
      }

      original._retry = true;
      refreshing = true;

      try {
        const refresh = localStorage.getItem('refresh_token');
        if (!refresh) throw new Error('No refresh token');

        const { data } = await axios.post<TokenResponse>(
          `${BASE_URL}/api/v1/auth/refresh`,
          { refresh_token: refresh }
        );
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);

        queue.forEach((cb) => cb(data.access_token));
        queue = [];

        original.headers!.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(error);
      } finally {
        refreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ─── Auth API ─────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post('/auth/register', data),
  login: (email: string, password: string) =>
    api.post<TokenResponse>('/auth/login', { email, password }),
  me: () => api.get('/auth/me'),
};

// ─── Tasks API ────────────────────────────────────────────────────────────────
export const tasksApi = {
  list: (params?: Record<string, unknown>) => api.get('/tasks', { params }),
  available: (params?: Record<string, unknown>) => api.get('/tasks/available', { params }),
  get: (id: number) => api.get(`/tasks/${id}`),
  create: (data: Record<string, unknown>) => api.post('/tasks', data),
  update: (id: number, data: Record<string, unknown>) => api.put(`/tasks/${id}`, data),
  delete: (id: number) => api.delete(`/tasks/${id}`),
};

// ─── Annotations API ──────────────────────────────────────────────────────────
export const annotationsApi = {
  submit: (data: { task_id: number; label: string; metadata?: Record<string, unknown> }) =>
    api.post('/annotations', data),
  myAnnotations: () => api.get('/annotations/my'),
  forTask: (taskId: number) => api.get(`/annotations/task/${taskId}`),
  verify: (id: number, status: string, comment?: string) =>
    api.put(`/annotations/${id}/verify`, { status, comment }),
};

// ─── Users API ────────────────────────────────────────────────────────────────
export const usersApi = {
  list: (params?: Record<string, unknown>) => api.get('/users', { params }),
  get: (id: number) => api.get(`/users/${id}`),
  updateRole: (id: number, role: string) => api.put(`/users/${id}/role`, { role }),
  deactivate: (id: number) => api.delete(`/users/${id}`),
};
