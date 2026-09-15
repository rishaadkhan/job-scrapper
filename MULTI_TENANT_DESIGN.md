# Multi-Tenant SaaS Design — Phase 6 Sketch

**Status:** Design doc only — no code changes.  
**Purpose:** Define the architectural changes needed to transform the single-user personal tool into a multi-tenant SaaS product, so Phase 6 implementation has a clear starting point with no blank-page decisions.

---

## Core Tenancy Model

**Recommended approach: Row-level tenant isolation (shared schema)**

Each resource table gains a `tenant_id UUID NOT NULL` foreign key. A `tenants` table owns the root record. All queries are automatically scoped with a `WHERE tenant_id = :current_tenant` guard enforced at the ORM/service layer.

This is simpler to operate than per-tenant databases, and Postgres RLS (Row Level Security) can enforce it at the DB level as an additional safety net.

```
tenants
  id          UUID PK
  name        TEXT
  plan        ENUM('free', 'pro', 'team')
  stripe_customer_id  TEXT
  stripe_subscription_id TEXT
  created_at  TIMESTAMPTZ

users
  id          UUID PK
  tenant_id   UUID FK → tenants.id
  email       TEXT UNIQUE within tenant
  role        ENUM('admin', 'viewer')
  password_hash TEXT
  created_at  TIMESTAMPTZ

companies           -- gains tenant_id FK
jobs                -- gains tenant_id FK
scrape_runs         -- gains tenant_id FK
filter_configs      -- gains tenant_id FK (one active per tenant)
export_records      -- gains tenant_id FK
```

**Migration path from Phase 5:** All existing rows get a single seed tenant (`tenant_id = '00000000-...'`), the current admin user is assigned to it. A subsequent Alembic migration adds `NOT NULL` constraints once all rows are backfilled.

---

## Per-User Resume Storage & Isolation

| Concern | Decision |
|---|---|
| Storage backend | DB blob (`BYTEA`) for ≤ 1 MB resumes; S3-compatible store (Cloudflare R2 or AWS S3) for larger files |
| Path/key | `{tenant_id}/{user_id}/resume.md` — never cross-tenant accessible |
| Encryption | AES-256-GCM at rest via S3 SSE-C or server-managed keys; DB blobs encrypted with a per-tenant KMS key |
| Access | Resume is read once per scrape run by the scorer; it is **never** exposed via an API response |
| Upload API | `PUT /me/resume` (multipart, max 2 MB, `.md`/`.txt`/`.pdf`) — PDF is converted to text server-side |

```
resume_files
  id         UUID PK
  tenant_id  UUID FK
  user_id    UUID FK
  s3_key     TEXT       -- null if stored in DB
  content    BYTEA      -- null if stored in S3
  size_bytes INT
  created_at TIMESTAMPTZ
  updated_at TIMESTAMPTZ
```

---

## Company/Filter Templates vs. Per-Tenant Overrides

**Pattern: Global template + per-tenant override layer**

A `SYSTEM` tenant (id = nil / sentinel) owns a curated default `companies` list and a default `filter_configs` row. When a new tenant signs up they inherit the system defaults. Any edits create per-tenant override rows. The scraper loads: per-tenant overrides first, then falls back to system defaults.

```
company_overrides
  id              UUID PK
  tenant_id       UUID FK
  base_company_id UUID FK → companies(id)  -- null = new company added by tenant
  active          BOOL     -- can suppress system companies
  ats             TEXT     -- override ATS platform
  ats_token       TEXT
  location_filter TEXT[]
  updated_at      TIMESTAMPTZ
```

For filters, the pattern is simpler: `filter_configs` already has one row per tenant. Phase 6 just makes the seeding automatic on tenant creation.

---

## JWT & Auth Changes

Current single-user JWT claims:
```json
{ "sub": "user@email.com", "role": "admin" }
```

Multi-tenant JWT claims:
```json
{ "sub": "user-uuid", "tenant_id": "tenant-uuid", "role": "admin", "plan": "pro" }
```

**Changes needed:**
- All `get_current_user` dependencies extract `tenant_id` from the token and attach it to the DB session context
- A `TenantContext` dependency (similar to Flask's `g`) propagates `tenant_id` into every CRUD call
- Per-tenant API key support: `api_keys` table with hashed keys, looked up as an alternative to JWT for server-to-server calls (CI pipelines, cron jobs)

---

## Billing Hook: Stripe Integration Sketch

**Flow:**
1. User picks a plan on the `/pricing` page
2. Frontend calls `POST /billing/checkout-session` → backend creates a Stripe Checkout Session and returns the URL
3. User completes payment on Stripe-hosted page → Stripe webhook fires `checkout.session.completed`
4. Webhook handler at `POST /billing/webhook`:
   - Validates Stripe signature (`stripe.Webhook.construct_event`)
   - Updates `tenants.plan` and `tenants.stripe_subscription_id`
   - Provisions any plan-gated features (e.g. raises `DIGEST_TOP_N` limit)
5. Subscription changes (upgrade/downgrade/cancel) flow through `customer.subscription.updated` / `customer.subscription.deleted` webhooks identically

**Plan limits enforced in code (not DB schema):**

| Feature | Free | Pro | Team |
|---|---|---|---|
| Companies | 50 | Unlimited | Unlimited |
| Scrape frequency | Weekly | Daily | Daily |
| DIGEST_TOP_N | 5 | 20 | 50 |
| Export history | 7 days | 30 days | 90 days |
| Users per tenant | 1 | 1 | 10 |
| LLM bullets | — | ✓ | ✓ |

Limits are checked at the service layer, not the DB layer, so adjusting them is a config change, not a migration.

---

## Database: SQLite → Postgres Migration

The `DATABASE_URL` env var already handles the `postgresql+asyncpg://` prefix. The full migration steps:

1. `alembic init alembic` + `alembic revision --autogenerate -m "add_tenant_id"` to generate the schema migration
2. `pg_restore` to seed Postgres from an SQLite dump (via `sqlite3 … .dump` → `pgloader`)
3. Fly.io: attach a Postgres cluster (`fly postgres create`) and set `DATABASE_URL` secret

No application code changes are needed beyond the above schema migration — the async SQLAlchemy layer is already DB-agnostic.

---

## Phase 6 Implementation Order

1. Add `tenants` table + Alembic migration framework
2. Backfill `tenant_id` on all existing tables
3. Add `TenantContext` dependency + scope all queries
4. Resume upload API + S3 integration
5. Global template + per-tenant override for companies
6. Stripe billing integration (checkout + webhooks)
7. Invite flow for team plan (email invites, role selection)
8. Admin super-user panel (tenant management, plan overrides)
