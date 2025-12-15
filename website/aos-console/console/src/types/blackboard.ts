export interface BlackboardEntry {
  key: string;
  value: unknown;
  value_type: 'string' | 'integer' | 'json';
  ttl_seconds: number | null;
  expires_at: string | null;
  is_locked: boolean;
  lock_owner: string | null;
  lock_expires_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BlackboardStats {
  total_keys: number;
  locked_keys: number;
  expiring_soon: number;
  by_pattern: Array<{
    pattern: string;
    count: number;
  }>;
}

export interface SetKeyRequest {
  value: unknown;
  value_type?: 'string' | 'integer' | 'json';
  ttl_seconds?: number;
}

export interface LockResult {
  success: boolean;
  lock_id: string;
  expires_at: string;
  waited_ms?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit?: number;
  page_size?: number;
  has_more?: boolean;
}
