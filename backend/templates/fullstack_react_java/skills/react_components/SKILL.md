---
name: react_components
description: Build React TypeScript components using functional components, hooks, state management, props typing, and proper folder organization
---

# React Components Skill

## Overview
This skill covers how to build well-structured React components with TypeScript for a fullstack application backed by a Spring Boot API.

## Project Structure

Organize components using a feature-based folder structure:

```
src/
  components/
    ui/                  # Reusable generic UI components
      Button/
        Button.tsx
        Button.styles.ts
        Button.test.tsx
        index.ts
      Input/
      Modal/
    layout/              # Layout components
      Header/
      Sidebar/
      PageLayout/
  features/              # Feature modules
    users/
      components/
        UserList.tsx
        UserForm.tsx
        UserCard.tsx
      hooks/
        useUsers.ts
        useUserForm.ts
      types/
        user.types.ts
      services/
        user.service.ts
      index.ts
    products/
      components/
      hooks/
      types/
  hooks/                 # Shared custom hooks
    useDebounce.ts
    usePagination.ts
  types/                 # Shared TypeScript types
    api.types.ts
    common.types.ts
  utils/                 # Utility functions
    formatters.ts
    validators.ts
```

Each component folder should have an `index.ts` barrel file:

```typescript
// components/ui/Button/index.ts
export { Button } from './Button';
export type { ButtonProps } from './Button';
```

## Functional Component Pattern

Always use functional components with explicit typing:

```typescript
import { useState, useCallback } from 'react';

interface UserCardProps {
  user: User;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  isEditable?: boolean;
}

export const UserCard: React.FC<UserCardProps> = ({
  user,
  onEdit,
  onDelete,
  isEditable = true,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleEdit = useCallback(() => {
    onEdit(user.id);
  }, [onEdit, user.id]);

  const handleDelete = useCallback(() => {
    onDelete(user.id);
  }, [onDelete, user.id]);

  return (
    <div className="user-card">
      <h3>{user.name}</h3>
      <p>{user.email}</p>
      {isExpanded && (
        <div className="user-card__details">
          <p>{user.bio}</p>
        </div>
      )}
      <button onClick={() => setIsExpanded(!isExpanded)}>
        {isExpanded ? 'Show less' : 'Show more'}
      </button>
      {isEditable && (
        <div className="user-card__actions">
          <button onClick={handleEdit}>Edit</button>
          <button onClick={handleDelete}>Delete</button>
        </div>
      )}
    </div>
  );
};
```

## Props Typing Rules

1. Define props as an `interface` (not `type`) so consumers can extend them.
2. Mark optional props with `?` and provide defaults via destructuring.
3. Use `React.ReactNode` for children, `React.CSSProperties` for style props.
4. For event handlers, use React's built-in event types.

```typescript
interface FormFieldProps {
  label: string;
  name: string;
  value: string;
  error?: string;
  required?: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  children?: React.ReactNode;
}
```

For components that wrap native HTML elements, extend the native props:

```typescript
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  loading = false,
  children,
  disabled,
  ...rest
}) => (
  <button
    className={`btn btn--${variant}`}
    disabled={disabled || loading}
    {...rest}
  >
    {loading ? <Spinner size="sm" /> : children}
  </button>
);
```

## Hooks

### useState
Use for simple local state. Always type the generic when the initial value does not convey the full type:

```typescript
const [user, setUser] = useState<User | null>(null);
const [items, setItems] = useState<Product[]>([]);
```

### useEffect
Use for side effects. Always include a cleanup function when subscribing to external resources:

```typescript
useEffect(() => {
  const controller = new AbortController();

  const fetchData = async () => {
    try {
      const data = await userService.getAll(controller.signal);
      setUsers(data);
    } catch (err) {
      if (!controller.signal.aborted) {
        setError('Failed to load users');
      }
    }
  };

  fetchData();

  return () => controller.abort();
}, []);
```

### Custom Hooks
Extract reusable logic into custom hooks. Name them with the `use` prefix:

```typescript
// hooks/usePagination.ts
import { useState, useMemo } from 'react';

interface UsePaginationOptions {
  totalItems: number;
  pageSize?: number;
  initialPage?: number;
}

interface UsePaginationReturn {
  currentPage: number;
  totalPages: number;
  goToPage: (page: number) => void;
  nextPage: () => void;
  prevPage: () => void;
  startIndex: number;
  endIndex: number;
}

export function usePagination({
  totalItems,
  pageSize = 10,
  initialPage = 1,
}: UsePaginationOptions): UsePaginationReturn {
  const [currentPage, setCurrentPage] = useState(initialPage);

  const totalPages = Math.ceil(totalItems / pageSize);

  const goToPage = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalItems);

  return useMemo(
    () => ({
      currentPage,
      totalPages,
      goToPage,
      nextPage: () => goToPage(currentPage + 1),
      prevPage: () => goToPage(currentPage - 1),
      startIndex,
      endIndex,
    }),
    [currentPage, totalPages, startIndex, endIndex]
  );
}
```

### useReducer
Use for complex state with multiple related transitions:

```typescript
interface FormState {
  values: Record<string, string>;
  errors: Record<string, string>;
  isSubmitting: boolean;
}

type FormAction =
  | { type: 'SET_FIELD'; field: string; value: string }
  | { type: 'SET_ERROR'; field: string; error: string }
  | { type: 'SUBMIT_START' }
  | { type: 'SUBMIT_SUCCESS' }
  | { type: 'SUBMIT_FAILURE'; errors: Record<string, string> }
  | { type: 'RESET' };

function formReducer(state: FormState, action: FormAction): FormState {
  switch (action.type) {
    case 'SET_FIELD':
      return {
        ...state,
        values: { ...state.values, [action.field]: action.value },
        errors: { ...state.errors, [action.field]: '' },
      };
    case 'SET_ERROR':
      return {
        ...state,
        errors: { ...state.errors, [action.field]: action.error },
      };
    case 'SUBMIT_START':
      return { ...state, isSubmitting: true };
    case 'SUBMIT_SUCCESS':
      return { ...state, isSubmitting: false, errors: {} };
    case 'SUBMIT_FAILURE':
      return { ...state, isSubmitting: false, errors: action.errors };
    case 'RESET':
      return { values: {}, errors: {}, isSubmitting: false };
    default:
      return state;
  }
}
```

## State Management with Context

For shared state across a feature, use React Context with a custom provider:

```typescript
// features/auth/AuthContext.tsx
import { createContext, useContext, useState, useCallback, ReactNode } from 'react';

interface AuthUser {
  id: string;
  name: string;
  email: string;
  roles: string[];
}

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);

  const login = useCallback(async (email: string, password: string) => {
    const response = await authService.login({ email, password });
    setUser(response.user);
    localStorage.setItem('token', response.token);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem('token');
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated: !!user, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

## Component Patterns

### Controlled Form Component

```typescript
interface ContactFormProps {
  initialValues?: Partial<ContactFormValues>;
  onSubmit: (values: ContactFormValues) => Promise<void>;
}

interface ContactFormValues {
  name: string;
  email: string;
  message: string;
}

export const ContactForm: React.FC<ContactFormProps> = ({
  initialValues,
  onSubmit,
}) => {
  const [values, setValues] = useState<ContactFormValues>({
    name: initialValues?.name ?? '',
    email: initialValues?.email ?? '',
    message: initialValues?.message ?? '',
  });
  const [errors, setErrors] = useState<Partial<ContactFormValues>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setValues((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
  };

  const validate = (): boolean => {
    const newErrors: Partial<ContactFormValues> = {};
    if (!values.name.trim()) newErrors.name = 'Name is required';
    if (!values.email.trim()) newErrors.email = 'Email is required';
    if (!values.message.trim()) newErrors.message = 'Message is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setIsSubmitting(true);
    try {
      await onSubmit(values);
    } catch {
      setErrors({ name: 'Submission failed. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} noValidate>
      <FormField
        label="Name"
        name="name"
        value={values.name}
        error={errors.name}
        onChange={handleChange}
        required
      />
      <FormField
        label="Email"
        name="email"
        value={values.email}
        error={errors.email}
        onChange={handleChange}
        required
      />
      <textarea
        name="message"
        value={values.message}
        onChange={handleChange}
      />
      {errors.message && <span className="error">{errors.message}</span>}
      <Button type="submit" loading={isSubmitting}>
        Send
      </Button>
    </form>
  );
};
```

### List with Loading and Empty State

```typescript
interface DataListProps<T> {
  items: T[];
  loading: boolean;
  error: string | null;
  renderItem: (item: T) => React.ReactNode;
  keyExtractor: (item: T) => string;
  emptyMessage?: string;
}

export function DataList<T>({
  items,
  loading,
  error,
  renderItem,
  keyExtractor,
  emptyMessage = 'No items found.',
}: DataListProps<T>) {
  if (loading) return <Spinner />;
  if (error) return <ErrorAlert message={error} />;
  if (items.length === 0) return <p>{emptyMessage}</p>;

  return (
    <ul className="data-list">
      {items.map((item) => (
        <li key={keyExtractor(item)}>{renderItem(item)}</li>
      ))}
    </ul>
  );
}
```

## Rules to Follow

1. Never use `any` -- always provide explicit types.
2. Keep components focused: one component, one responsibility.
3. Extract business logic into custom hooks; keep components presentational.
4. Use `useCallback` for event handlers passed as props to child components.
5. Use `useMemo` for expensive computations, not for every variable.
6. Prefer controlled components for forms.
7. Always handle loading, error, and empty states in data-fetching components.
8. Use barrel exports (`index.ts`) for clean imports.
9. Co-locate tests next to the component they test.
10. Avoid prop drilling beyond two levels -- use Context or composition instead.
