// ─── Enums ────────────────────────────────────────────────────────────────────

export type UserRole = 'admin' | 'manager' | 'annotator';
export type TaskType = 'image_classification' | 'text_classification' | 'ner' | 'sentiment' | 'bounding_box';
export type TaskStatus = 'draft' | 'active' | 'completed' | 'archived';
export type AnnotationStatus = 'pending' | 'verified' | 'rejected';

// ─── Entities ─────────────────────────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface Dataset {
  id: number;
  name: string;
  description: string | null;
  task_type: TaskType;
  labels: string[];
  creator_id: number;
  created_at: string;
}

export interface Task {
  id: number;
  title: string;
  description: string | null;
  dataset_id: number;
  creator_id: number;
  status: TaskStatus;
  data: Record<string, unknown>;
  annotations_required: number;
  reward_points: number;
  annotation_count: number;
  created_at: string;
  updated_at: string;
}

export interface Annotation {
  id: number;
  task_id: number;
  annotator_id: number;
  label: string;
  metadata: Record<string, unknown> | null;
  status: AnnotationStatus;
  verified_by: number | null;
  comment: string | null;
  created_at: string;
}

// ─── API ──────────────────────────────────────────────────────────────────────

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
}
