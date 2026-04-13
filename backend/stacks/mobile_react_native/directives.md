# Directives — React Native Mobile

IMMUTABLE rules.

## Architecture
1. Use Expo SDK unless ejection is explicitly required.
2. Navigation MUST use React Navigation (stack/tab/drawer).
3. State management: Zustand or Redux Toolkit (choose one, stick to it).
4. API calls MUST be in services/ layer, never in components.

## Code Quality
5. TypeScript strict mode enabled — no `any`.
6. Components MUST be functional with hooks.
7. Styles MUST use StyleSheet.create — no inline styles for reusable components.
8. NEVER use deprecated APIs (ScrollView + FlatList confusion, etc.)

## Performance
9. Lists MUST use FlatList/SectionList — never ScrollView for large lists.
10. Images MUST use proper resolution + caching (Expo Image).
11. Avoid re-renders: use memo, useCallback, useMemo appropriately.

## Security
12. Secrets MUST use expo-secure-store — never AsyncStorage.
13. Deep links MUST validate parameters.
14. API tokens MUST be stored securely.

## Testing
15. Jest for unit tests, Detox for E2E.
16. Test hooks with @testing-library/react-hooks.
