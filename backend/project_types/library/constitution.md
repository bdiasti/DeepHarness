# Constitution — Library / Package

IMMUTABLE rules for reusable libraries.

## API Stability (CRITICAL)
1. Public API MUST follow semantic versioning (MAJOR.MINOR.PATCH).
2. Breaking changes MUST bump MAJOR version.
3. Every breaking change MUST be documented in CHANGELOG.md.
4. Deprecations MUST be announced 1 minor version before removal.

## Documentation
5. README MUST have: install, quick start, API reference, examples.
6. Every public function/class MUST have doc comments.
7. Examples directory MUST have runnable code.
8. API reference MUST be auto-generated (Typedoc, Sphinx, Javadoc).

## Testing
9. Test coverage MUST be >90% for public API.
10. Tests MUST run on CI for every PR.
11. Matrix tests across supported versions (Node LTS, Python versions, etc.).

## Publishing
12. MUST include LICENSE file (MIT, Apache, etc.).
13. Build artifacts MUST NOT include tests/dev files.
14. Version number MUST match git tag.

## What's NOT allowed
- Do NOT break API without MAJOR bump.
- Do NOT publish without CHANGELOG entry.
- Do NOT ship with failing tests.
- Do NOT include credentials, tokens, or .env in package.
