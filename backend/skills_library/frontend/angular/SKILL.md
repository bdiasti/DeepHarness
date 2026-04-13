---
name: angular
description: Angular 17+ with standalone components, signals, RxJS, typed forms
---

# Angular 17+

Modern Angular using standalone components, signals for reactivity, RxJS for streams, and typed reactive forms.

## Standalone Component with Signals

```typescript
import { Component, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-counter',
  standalone: true,
  imports: [CommonModule],
  template: `
    <button (click)="increment()">Count: {{ count() }}</button>
    <p>Doubled: {{ doubled() }}</p>
  `,
})
export class CounterComponent {
  count = signal(0);
  doubled = computed(() => this.count() * 2);
  increment() { this.count.update(v => v + 1); }
}
```

## Service with HttpClient and RxJS

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, map, throwError } from 'rxjs';

export interface User { id: number; name: string; }

@Injectable({ providedIn: 'root' })
export class UserService {
  private http = inject(HttpClient);
  private base = '/api/users';

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(this.base).pipe(
      map(users => users.filter(u => !!u.name)),
      catchError(err => throwError(() => new Error('Failed: ' + err.message))),
    );
  }
}
```

## Typed Reactive Forms

```typescript
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <form [formGroup]="form" (ngSubmit)="submit()">
      <input formControlName="email" />
      <input formControlName="password" type="password" />
      <button [disabled]="form.invalid">Login</button>
    </form>
  `,
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });
  submit() {
    if (this.form.valid) console.log(this.form.getRawValue());
  }
}
```

## Routing (Standalone)

```typescript
// app.routes.ts
import { Routes } from '@angular/router';
export const routes: Routes = [
  { path: '', loadComponent: () => import('./home').then(m => m.HomeComponent) },
  { path: 'users/:id', loadComponent: () => import('./user').then(m => m.UserComponent) },
];

// main.ts
import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
bootstrapApplication(AppComponent, {
  providers: [provideRouter(routes), provideHttpClient()],
});
```

## Tips
- Prefer `inject()` over constructor injection in modern code.
- Use `signal()` for local state, `computed()` for derived, `effect()` for side effects.
- Convert RxJS to signals via `toSignal()` from `@angular/core/rxjs-interop`.
- Use `OnPush` change detection + signals for performance.
