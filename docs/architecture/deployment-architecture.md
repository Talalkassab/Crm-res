# Deployment Architecture

## Deployment Strategy

**Frontend Deployment:**
- **Platform:** Vercel (optimized for Next.js)
- **Build Command:** `turbo run build --filter=dashboard`
- **Output Directory:** `apps/dashboard/out`
- **CDN/Edge:** Vercel Edge Network with global distribution

**Backend Deployment:**
- **Platform:** AWS ECS Fargate with Application Load Balancer
- **Build Command:** Docker multi-stage builds
- **Deployment Method:** Blue-green deployment via ECS service updates

## Environments

| Environment | Frontend URL | Backend URL | Purpose |
|-------------|-------------|-------------|---------|
| Development | http://localhost:3000 | http://localhost:8000 | Local development |
| Staging | https://staging.crm-res.com | https://api-staging.crm-res.com | Pre-production testing |
| Production | https://app.crm-res.com | https://api.crm-res.com | Live environment |
