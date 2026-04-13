---
name: flutter
description: Flutter with Dart — widgets, state management (Riverpod/Bloc), navigation
---

# Flutter

Single Dart codebase compiled to native iOS/Android/web/desktop. Everything is a **Widget**.

## Bootstrap

```bash
flutter create my_app
cd my_app
flutter run            # picks connected device
flutter pub add riverpod flutter_riverpod go_router dio freezed_annotation
flutter pub add --dev build_runner freezed json_serializable
```

## Widget Basics

```dart
class ProductCard extends StatelessWidget {
  const ProductCard({super.key, required this.name, required this.price});
  final String name; final double price;

  @override
  Widget build(BuildContext ctx) => Card(
    child: ListTile(
      title: Text(name, style: Theme.of(ctx).textTheme.titleMedium),
      trailing: Text('\$${price.toStringAsFixed(2)}'),
      onTap: () => GoRouter.of(ctx).push('/product/$name'),
    ),
  );
}
```

Stateless vs Stateful: use Stateful only when local mutable state is needed; otherwise lift state up to a provider.

## State Management — Riverpod (recommended)

```dart
// providers.dart
final apiProvider = Provider((ref) => Dio(BaseOptions(baseUrl: 'https://api.x')));

final productsProvider = FutureProvider<List<Product>>((ref) async {
  final r = await ref.watch(apiProvider).get('/products');
  return (r.data as List).map(Product.fromJson).toList();
});

// widget
class ProductsPage extends ConsumerWidget {
  @override
  Widget build(BuildContext ctx, WidgetRef ref) {
    final async = ref.watch(productsProvider);
    return async.when(
      data: (items) => ListView(children: items.map((p) => ProductCard(name: p.name, price: p.price)).toList()),
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (e, _) => Center(child: Text('$e')),
    );
  }
}
```

## Bloc Alternative

```dart
class CounterCubit extends Cubit<int> {
  CounterCubit() : super(0);
  void inc() => emit(state + 1);
}

BlocProvider(create: (_) => CounterCubit(),
  child: BlocBuilder<CounterCubit, int>(
    builder: (ctx, n) => Text('$n'),
  ));
```

Use Bloc for complex event-driven flows; Riverpod for most apps (less boilerplate).

## Navigation (go_router)

```dart
final router = GoRouter(routes: [
  GoRoute(path: '/', builder: (_, __) => const HomePage()),
  GoRoute(path: '/product/:id', builder: (_, s) => ProductPage(id: s.pathParameters['id']!)),
  ShellRoute(builder: (_, __, child) => MainScaffold(child: child), routes: [
    GoRoute(path: '/cart', builder: (_, __) => const CartPage()),
  ]),
]);

MaterialApp.router(routerConfig: router);
```

## Platform-Specific

```dart
import 'dart:io' show Platform;
final pad = Platform.isIOS ? 16.0 : 8.0;

// Native APIs via platform channels or pub.dev packages:
// camera, geolocator, shared_preferences, flutter_secure_storage, path_provider
```

## Performance

- `const` constructors everywhere possible (skips rebuilds)
- `ListView.builder` for long lists (lazy)
- Keep `build()` cheap; extract widgets; avoid big widget trees in one method
- Profile with DevTools: `flutter run --profile`
- Use `RepaintBoundary` around expensive static subtrees

## Build & Ship

```bash
flutter build apk --release
flutter build appbundle --release     # Play Store
flutter build ipa --release           # App Store (macOS)
flutter test                          # unit/widget tests
flutter test integration_test/        # e2e
```

Config per env with `--dart-define=API_URL=...` or flavors.
