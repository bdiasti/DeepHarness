---
name: vue
description: Vue 3 Composition API with script setup, Pinia state, composables
---

# Vue 3

Modern Vue using `<script setup>` Composition API, Pinia for state, and reusable composables.

## Component with script setup

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';

interface Props { initial?: number }
const props = withDefaults(defineProps<Props>(), { initial: 0 });
const emit = defineEmits<{ change: [value: number] }>();

const count = ref(props.initial);
const doubled = computed(() => count.value * 2);

function increment() {
  count.value++;
  emit('change', count.value);
}

onMounted(() => console.log('mounted'));
</script>

<template>
  <button @click="increment">Count: {{ count }} (x2 = {{ doubled }})</button>
</template>
```

## Pinia Store

```typescript
// stores/user.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useUserStore = defineStore('user', () => {
  const user = ref<{ id: number; name: string } | null>(null);
  const isLoggedIn = computed(() => user.value !== null);

  async function login(email: string, password: string) {
    const res = await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    user.value = await res.json();
  }
  function logout() { user.value = null; }

  return { user, isLoggedIn, login, logout };
});
```

## Composable

```typescript
// composables/useFetch.ts
import { ref, watchEffect, type Ref } from 'vue';

export function useFetch<T>(url: Ref<string> | string) {
  const data = ref<T | null>(null);
  const error = ref<Error | null>(null);
  const loading = ref(false);

  watchEffect(async () => {
    loading.value = true;
    try {
      const u = typeof url === 'string' ? url : url.value;
      data.value = await (await fetch(u)).json();
    } catch (e) {
      error.value = e as Error;
    } finally {
      loading.value = false;
    }
  });

  return { data, error, loading };
}
```

## Router & App Setup

```typescript
// main.ts
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { createRouter, createWebHistory } from 'vue-router';
import App from './App.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('./views/Home.vue') },
    { path: '/users/:id', component: () => import('./views/User.vue'), props: true },
  ],
});

createApp(App).use(createPinia()).use(router).mount('#app');
```

## Tips
- Prefer `ref` over `reactive` for consistency; use `.value` in scripts (auto-unwrapped in templates).
- Use `defineProps`/`defineEmits` with TypeScript generics for type safety.
- Extract logic into composables (`useX` functions) for reuse.
- Use `storeToRefs(store)` to destructure Pinia state without losing reactivity.
