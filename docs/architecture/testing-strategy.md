# Testing Strategy

## Testing Pyramid

```text
       E2E Tests (10%)
      /              \
   Integration Tests (20%)
   /                      \
Frontend Unit (35%)  Backend Unit (35%)
```

## Test Organization

### Frontend Tests
```text
apps/dashboard/tests/
├── components/          # Component unit tests
├── hooks/              # Custom hook tests  
├── pages/              # Page integration tests
├── e2e/                # Playwright E2E tests
└── setup.ts            # Test configuration
```

### Backend Tests
```text
services/*/tests/
├── unit/               # Unit tests
├── integration/        # API integration tests
├── fixtures/           # Test data
└── conftest.py         # Pytest configuration
```
