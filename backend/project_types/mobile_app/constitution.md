# Constitution — Mobile App (React Native + Expo)

IMMUTABLE rules.

## Stack (FIXED)
1. MUST use Expo (managed workflow or prebuild, NOT bare RN).
2. Navigation MUST use React Navigation v7+.
3. State management: Zustand OR Redux Toolkit (choose and stick).
4. TypeScript strict mode — NO `any`.

## Mobile-specific
5. Secrets MUST use expo-secure-store (NEVER AsyncStorage).
6. Images MUST use Expo Image with caching.
7. Lists MUST use FlatList/FlashList — NEVER ScrollView for lists.
8. Screens MUST be lazy-loaded via navigation.

## Performance
9. Use React.memo, useCallback, useMemo for expensive renders.
10. Avoid re-renders caused by unstable object/array deps.
11. Native animations via Reanimated 3+ (no JS-based animations).

## Testing
12. Jest for unit tests, Detox for E2E.
13. Critical flows (login, checkout) MUST have E2E.

## What's NOT allowed
- Do NOT use bare React Native workflow unless explicitly needed.
- Do NOT store tokens in AsyncStorage (use SecureStore).
- Do NOT use `any` type.
