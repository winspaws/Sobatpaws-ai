# Sobatpaws Architecture Decisions

> This file is maintained by Architect profile.
> Last updated: 2025-06-19

---

## ✅ Accepted Decisions

| ID | Tanggal | Judul | Status | ADR |
|----|---------|-------|--------|-----|
| 001 | 2025-06-19 | PostgreSQL Migration | Proposed | [docs/adr/ADR-001-postgresql-migration.md](docs/adr/ADR-001-postgresql-migration.md) |
| 002 | 2025-06-19 | Frontend Telekonsultasi Architecture | Proposed | [docs/adr/ADR-002-frontend-telekonsultasi.md](docs/adr/ADR-002-frontend-telekonsultasi.md) |

---

## 📋 Stack Standar

### Backend
- **Framework**: FastAPI 0.115+
- **Database**: PostgreSQL 16
- **ORM**: SQLAlchemy 2.0
- **Migration**: Alembic
- **ML**: Scikit-learn, XGBoost
- **AI**: OpenAI GPT-4o Mini / BytePlus Doubao

### Frontend
- **Framework**: Next.js 16 App Router
- **Language**: TypeScript Strict
- **State**: TanStack Query v5
- **Realtime**: Socket.io
- **UI**: shadcn/ui + Tailwind v3

### Infra
- **Container**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Deployment**: Fly.io
- **Monitoring**: Prometheus + Grafana

---

## 🚫 Rejected Decisions

| Tanggal | Keputusan | Alasan Penolakan |
|---------|-----------|------------------|
| 2025-06-19 | MongoDB sebagai primary database | Data klinis membutuhkan schema ketat, referential integrity, dan ACID compliance yang tidak dapat diandalkan pada MongoDB |
| 2025-06-19 | Vanilla React SPA tanpa framework | Butuh routing, SSR, dan optimasi performa yang disediakan Next.js secara out of the box |

---

## ⏳ Pending Decisions

1.  Authentication provider (Auth0 vs Supabase vs Custom)
2.  File storage untuk foto konsultasi (S3 vs Cloudflare R2)
3.  SMS / Whatsapp notification provider
4.  Logging dan error tracking platform
