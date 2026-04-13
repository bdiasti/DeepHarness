---
name: react_native
description: React Native with Expo, navigation, native modules, platform-specific code
---

# React Native (Expo)

Cross-platform mobile apps with JS/TS sharing ~90% of code across iOS/Android.

## Bootstrap (Expo)

```bash
npx create-expo-app@latest my-app -t expo-template-blank-typescript
cd my-app && npx expo start
# run on device: scan QR in Expo Go; or npx expo run:ios / run:android
```

Prefer **Expo SDK** for managed workflow; eject (prebuild) only when a native module isn't available as a config plugin.

## Navigation (Expo Router — file-based)

```
app/
  _layout.tsx          # Stack root
  index.tsx            # /
  (tabs)/_layout.tsx   # Tabs
  (tabs)/home.tsx
  orders/[id].tsx      # dynamic route
```

```tsx
// app/_layout.tsx
import { Stack } from "expo-router";
export default () => <Stack screenOptions={{ headerShown: true }} />;

// navigate
import { router } from "expo-router";
router.push(`/orders/${id}`);
```

Alternative: `@react-navigation/native` with `NavigationContainer` + stack/tab/drawer navigators.

## Platform-Specific Code

```tsx
import { Platform, StyleSheet } from "react-native";

const s = StyleSheet.create({
  header: {
    paddingTop: Platform.OS === "ios" ? 44 : 24,
    ...Platform.select({ ios: { shadowOpacity: 0.1 }, android: { elevation: 4 } }),
  },
});
```

File-level: `Button.ios.tsx` / `Button.android.tsx` are auto-resolved by Metro.

## Native Modules

- **Use Expo modules first**: `expo-camera`, `expo-location`, `expo-notifications`, `expo-secure-store`, `expo-file-system`, `expo-image-picker`.
- For custom native code, write an **Expo Module** (`npx create-expo-module`) exposing a TS API; build with EAS.
- Old-style: `NativeModules` + bridging (Swift/Kotlin) — prefer the new arch (TurboModules/Fabric) for new code.

```ts
import * as SecureStore from "expo-secure-store";
await SecureStore.setItemAsync("token", jwt);
const t = await SecureStore.getItemAsync("token");
```

## State & Data

- **State**: Zustand or Redux Toolkit for global; React Context for small trees
- **Server state**: TanStack Query handles caching/retries/offline
- **Forms**: react-hook-form + zod
- **Storage**: `expo-secure-store` (secrets), `AsyncStorage` (non-sensitive), SQLite via `expo-sqlite`

## Performance

- Use `FlatList`/`FlashList` for long lists (never `.map` hundreds of items)
- Memoize: `React.memo`, `useCallback`, stable keys
- Hermes engine enabled by default on Expo; turn on in `app.json` if not
- Optimize images with `expo-image` (caching + memory efficient)
- Avoid inline arrow functions in render of list items

## Build & Ship (EAS)

```bash
npm i -g eas-cli && eas login
eas build:configure
eas build -p ios --profile production
eas build -p android --profile production
eas submit -p ios   # App Store
eas update          # OTA JS updates (no store review)
```

Define profiles in `eas.json`; secrets via `eas secret:create`.
