---
name: api_integration
description: Connect a React TypeScript frontend to a Spring Boot Java backend using axios, API clients, error handling, loading states, and shared TypeScript types
---

# API Integration Skill

## Overview
This skill covers how to connect a React frontend to a Spring Boot backend with a clean, type-safe API layer that handles authentication, errors, and loading states.

## Project Structure for API Layer

```
src/
  api/
    client.ts              # Axios instance with interceptors
    endpoints/
      auth.api.ts          # Auth endpoints
      users.api.ts         # User endpoints
      products.api.ts      # Product endpoints
    index.ts               # Barrel export
  types/
    api.types.ts           # Shared API types (PageResponse, ErrorResponse)
    models/
      user.types.ts        # User-related types
      product.types.ts     # Product-related types
  hooks/
    useApi.ts              # Generic data-fetching hook
```

## Axios Client Setup

Create a configured Axios instance with interceptors for auth tokens and error handling:

```typescript
// api/client.ts
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Request interceptor: attach JWT token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 and transform errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorResponse>) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

## TypeScript Types from API Contracts

Define types that match the Spring Boot DTOs exactly:

```typescript
// types/api.types.ts

export interface ApiErrorResponse {
  status: number;
  message: string;
  timestamp: string;
}

export interface ValidationErrorResponse extends ApiErrorResponse {
  errors: Record<string, string>;
}

export interface PageResponse<T> {
  content: T[];
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
  last: boolean;
}

export interface PageParams {
  page?: number;
  size?: number;
  sortBy?: string;
}
```

```typescript
// types/models/user.types.ts

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  createdAt: string;
  updatedAt: string;
}

export enum UserRole {
  ADMIN = 'ADMIN',
  USER = 'USER',
  MODERATOR = 'MODERATOR',
}

export interface CreateUserRequest {
  name: string;
  email: string;
  password: string;
  role: UserRole;
}

export interface UpdateUserRequest {
  name?: string;
  email?: string;
  role?: UserRole;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}
```

## API Endpoint Modules

Group endpoints by resource. Each function returns typed promises:

```typescript
// api/endpoints/auth.api.ts
import { apiClient } from '../client';
import { AuthResponse, LoginRequest } from '../../types/models/user.types';

export const authApi = {
  login: (data: LoginRequest) =>
    apiClient.post<AuthResponse>('/auth/login', data).then((r) => r.data),

  register: (data: CreateUserRequest) =>
    apiClient.post<AuthResponse>('/auth/register', data).then((r) => r.data),

  me: () =>
    apiClient.get<User>('/auth/me').then((r) => r.data),
};
```

```typescript
// api/endpoints/users.api.ts
import { apiClient } from '../client';
import {
  User,
  CreateUserRequest,
  UpdateUserRequest,
} from '../../types/models/user.types';
import { PageResponse, PageParams } from '../../types/api.types';

export const usersApi = {
  list: (params?: PageParams) =>
    apiClient
      .get<PageResponse<User>>('/users', { params })
      .then((r) => r.data),

  getById: (id: number) =>
    apiClient.get<User>(`/users/${id}`).then((r) => r.data),

  create: (data: CreateUserRequest) =>
    apiClient.post<User>('/users', data).then((r) => r.data),

  update: (id: number, data: UpdateUserRequest) =>
    apiClient.put<User>(`/users/${id}`, data).then((r) => r.data),

  delete: (id: number) =>
    apiClient.delete<void>(`/users/${id}`).then((r) => r.data),

  search: (query: string, params?: PageParams) =>
    apiClient
      .get<PageResponse<User>>('/users/search', {
        params: { q: query, ...params },
      })
      .then((r) => r.data),
};
```

```typescript
// api/index.ts
export { apiClient } from './client';
export { authApi } from './endpoints/auth.api';
export { usersApi } from './endpoints/users.api';
export { productsApi } from './endpoints/products.api';
```

## Generic Data-Fetching Hook

A reusable hook that handles loading, error, and data states:

```typescript
// hooks/useApi.ts
import { useState, useEffect, useCallback } from 'react';
import { AxiosError } from 'axios';
import { ApiErrorResponse } from '../types/api.types';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiReturn<T> extends UseApiState<T> {
  refetch: () => void;
}

export function useApi<T>(
  fetcher: () => Promise<T>,
  dependencies: unknown[] = []
): UseApiReturn<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await fetcher();
      setState({ data, loading: false, error: null });
    } catch (err) {
      const message = extractErrorMessage(err);
      setState({ data: null, loading: false, error: message });
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}

function extractErrorMessage(err: unknown): string {
  if (err instanceof AxiosError) {
    const apiError = err.response?.data as ApiErrorResponse | undefined;
    if (apiError?.message) return apiError.message;
    if (err.message) return err.message;
  }
  if (err instanceof Error) return err.message;
  return 'An unexpected error occurred';
}
```

## Mutation Hook

For create/update/delete operations:

```typescript
// hooks/useMutation.ts
import { useState, useCallback } from 'react';
import { AxiosError } from 'axios';
import { ApiErrorResponse, ValidationErrorResponse } from '../types/api.types';

interface UseMutationReturn<TInput, TOutput> {
  mutate: (input: TInput) => Promise<TOutput | undefined>;
  loading: boolean;
  error: string | null;
  fieldErrors: Record<string, string>;
  reset: () => void;
}

export function useMutation<TInput, TOutput>(
  mutationFn: (input: TInput) => Promise<TOutput>
): UseMutationReturn<TInput, TOutput> {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const reset = useCallback(() => {
    setError(null);
    setFieldErrors({});
  }, []);

  const mutate = useCallback(
    async (input: TInput): Promise<TOutput | undefined> => {
      setLoading(true);
      reset();
      try {
        const result = await mutationFn(input);
        setLoading(false);
        return result;
      } catch (err) {
        setLoading(false);
        if (err instanceof AxiosError && err.response) {
          const data = err.response.data;
          if (isValidationError(data)) {
            setFieldErrors(data.errors);
            setError(data.message);
          } else if (isApiError(data)) {
            setError(data.message);
          } else {
            setError('An unexpected error occurred');
          }
        } else {
          setError('Network error. Please check your connection.');
        }
        return undefined;
      }
    },
    [mutationFn, reset]
  );

  return { mutate, loading, error, fieldErrors, reset };
}

function isApiError(data: unknown): data is ApiErrorResponse {
  return typeof data === 'object' && data !== null && 'message' in data && 'status' in data;
}

function isValidationError(data: unknown): data is ValidationErrorResponse {
  return isApiError(data) && 'errors' in data;
}
```

## Using the Hooks in Components

### Fetching a List

```typescript
import { usersApi } from '../../api';
import { useApi } from '../../hooks/useApi';

export const UserListPage: React.FC = () => {
  const [page, setPage] = useState(0);
  const { data, loading, error, refetch } = useApi(
    () => usersApi.list({ page, size: 20 }),
    [page]
  );

  if (loading) return <Spinner />;
  if (error) return <ErrorAlert message={error} onRetry={refetch} />;
  if (!data) return null;

  return (
    <div>
      <h1>Users</h1>
      <DataList
        items={data.content}
        loading={false}
        error={null}
        renderItem={(user) => <UserCard key={user.id} user={user} />}
        keyExtractor={(user) => String(user.id)}
      />
      <Pagination
        currentPage={data.page}
        totalPages={data.totalPages}
        onPageChange={setPage}
      />
    </div>
  );
};
```

### Creating a Resource

```typescript
import { usersApi } from '../../api';
import { useMutation } from '../../hooks/useMutation';
import { CreateUserRequest } from '../../types/models/user.types';

export const CreateUserPage: React.FC = () => {
  const navigate = useNavigate();
  const { mutate, loading, error, fieldErrors } = useMutation(usersApi.create);

  const handleSubmit = async (values: CreateUserRequest) => {
    const created = await mutate(values);
    if (created) {
      navigate(`/users/${created.id}`);
    }
  };

  return (
    <div>
      <h1>Create User</h1>
      {error && <ErrorAlert message={error} />}
      <UserForm
        onSubmit={handleSubmit}
        loading={loading}
        fieldErrors={fieldErrors}
      />
    </div>
  );
};
```

## Handling File Uploads

For multipart requests to Spring Boot:

```typescript
// api/endpoints/files.api.ts
export const filesApi = {
  upload: (file: File, onProgress?: (percent: number) => void) => {
    const formData = new FormData();
    formData.append('file', file);

    return apiClient.post<{ url: string }>('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        if (onProgress && event.total) {
          onProgress(Math.round((event.loaded * 100) / event.total));
        }
      },
    }).then((r) => r.data);
  },
};
```

## Environment Configuration

```env
# .env.development
VITE_API_BASE_URL=http://localhost:8080

# .env.production
VITE_API_BASE_URL=https://api.myapp.com
```

Set up proxy in `vite.config.ts` to avoid CORS during development:

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
});
```

## Rules to Follow

1. Never call `axios` directly in components -- always go through the `apiClient` and endpoint modules.
2. Always type API responses -- never use `any` or untyped `.data`.
3. Handle all three states in every data-fetching component: loading, error, and success.
4. Use interceptors for cross-cutting concerns (auth tokens, error transforms, logging).
5. Keep TypeScript types in sync with Spring Boot DTOs. When a backend DTO changes, update the corresponding frontend type.
6. Use environment variables for the API base URL -- never hardcode it.
7. Provide retry/refetch capability for failed requests.
8. Use `AbortController` or Axios cancel tokens for requests that should be cancelled on unmount.
9. Show field-level validation errors from the backend `ValidationErrorResponse` next to the corresponding form fields.
10. Use the Vite dev proxy to avoid CORS issues during local development.
