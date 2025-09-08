# Supabase Database Setup

This directory contains the database schema and configuration for the CRM-RES project.

## Setup Instructions

### 1. Create Supabase Project

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Create a new project
3. Wait for the project to be fully provisioned
4. Note down your project URL and API keys

### 2. Run Initial Schema

1. Open the SQL Editor in your Supabase dashboard
2. Copy and paste the contents of `schemas/initial-schema.sql`
3. Click "Run" to execute the schema creation

### 3. Seed Development Data (Optional)

For development and testing:

1. Copy and paste the contents of `seed-data.sql` in the SQL Editor
2. Click "Run" to populate with sample data

### 4. Update Environment Variables

Add these to your `.env` file:

```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_DATABASE_URL=postgresql://postgres:your-password@db.your-project-id.supabase.co:5432/postgres
```

## Database Schema Overview

### Core Tables

- **restaurants** - Multi-tenant root table for restaurant organizations
- **users** - Restaurant staff members with role-based access
- **customers** - WhatsApp customers with preferences and context
- **conversations** - WhatsApp conversation threads
- **messages** - Individual messages with AI processing metadata
- **feedback** - Customer feedback and ratings

### Key Features

- **Row Level Security (RLS)** - Enabled on all tables with appropriate policies
- **Multi-tenant Architecture** - Data isolation by restaurant_id
- **Arabic Text Search** - Full-text search indexes for Arabic content
- **JSONB Storage** - Flexible schema for preferences and metadata
- **PostGIS Support** - Location-based features for delivery zones
- **Audit Trails** - Automatic timestamp tracking with triggers

### Extensions Enabled

- **uuid-ossp** - UUID generation
- **postgis** - Geographical data support
- **pg_trgm** - Trigram matching for fuzzy text search

## Authentication & Authorization

### Supabase Auth Integration

The schema is designed to work with Supabase Auth:

1. **User Registration** - Users are created in both auth.users and public.users
2. **RLS Policies** - Enforce multi-tenant data isolation
3. **Role-Based Access** - Admin, Manager, and Staff roles with different permissions

### Sample RLS Policy

```sql
-- Users can only access customers from their restaurant
CREATE POLICY customers_policy ON customers FOR ALL USING (
    auth.uid() IN (SELECT id FROM users WHERE restaurant_id = customers.restaurant_id AND is_active = true)
);
```

## Performance Optimizations

### Indexes

- Primary keys and foreign keys automatically indexed
- Composite indexes for common query patterns
- GIN indexes for JSONB columns and full-text search
- Covering indexes for frequently accessed columns

### Query Optimization

- Use `restaurant_id` in WHERE clauses for partition elimination
- Leverage JSONB operators for flexible queries
- Use prepared statements for repeated queries

## Backup & Migrations

### Backup Strategy

- Supabase provides automatic daily backups
- Point-in-time recovery available
- Export capability for full database dumps

### Migration Management

- Store schema changes in numbered migration files
- Test migrations on staging before production
- Use transaction blocks for atomic schema updates

## Monitoring & Maintenance

### Key Metrics to Monitor

- Table sizes and growth rates
- Index usage and efficiency  
- Query performance and slow queries
- Connection pool utilization

### Regular Maintenance

- Analyze query patterns monthly
- Review and optimize slow queries
- Monitor storage usage and costs
- Update table statistics regularly

## Development Workflow

### Local Development

1. Use the seed data for consistent test scenarios
2. Create feature-specific test data as needed
3. Reset database state between test runs

### Testing

1. Run schema tests to validate constraints
2. Test RLS policies with different user roles
3. Performance test with realistic data volumes

## Security Considerations

### Data Protection

- All tables have RLS enabled
- Sensitive data encrypted in transit and at rest
- Regular security audits of policies and permissions

### Access Control

- Principle of least privilege for database access
- Regular review of user permissions
- Audit logs for all data access patterns