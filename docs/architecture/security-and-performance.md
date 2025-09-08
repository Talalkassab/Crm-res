# Security and Performance

## Security Requirements

**Frontend Security:**
- CSP Headers: `default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'`
- XSS Prevention: React's built-in escaping + Content Security Policy
- Secure Storage: Supabase handles JWT tokens securely, sensitive data in httpOnly cookies

**Backend Security:**
- Input Validation: Pydantic models with strict validation
- Rate Limiting: 1000 requests/hour per restaurant (configurable by tier)
- CORS Policy: Restricted to known frontend domains only

**Authentication Security:**
- Token Storage: JWTs in httpOnly cookies, refresh tokens in secure storage
- Session Management: Supabase Auth with automatic token refresh
- Password Policy: Enforced by Supabase (min 8 chars, complexity requirements)

## Performance Optimization

**Frontend Performance:**
- Bundle Size Target: <250KB initial JS bundle
- Loading Strategy: Route-based code splitting with Next.js
- Caching Strategy: Static assets cached 1 year, API responses 5 minutes

**Backend Performance:**
- Response Time Target: <200ms for 95% of API calls
- Database Optimization: Proper indexing, query optimization, connection pooling
- Caching Strategy: Redis for conversation state, PostgreSQL query cache
