# Sprint 4 Planning — HANDOFF

> Tanggal: 2026-06-27
> Profile: wins (PM)
> Task: t_5a6d47c2 — Sprint 4 Planning & Backlog

---

## ✅ Yang Dilakukan

### Sprint 4 Planning — Admin Panel Integration

Membuat 8 task Sprint 4 di Kanban board `naincode` dengan dependency chain:

| # | Task | Assignee | Priority | Dependencies |
|---|------|----------|----------|--------------|
| 1 | Data Model Alignment — Pet and User fields | backend | P1 | — |
| 2 | Alembic Migration — Schema Changes | backend | P1 | 1 |
| 3 | Integration Enhancement — Pre-Screening, Medical History, Dashboard Insights | backend | P1 | 1, 2 |
| 4 | Vision Analysis for Admin — Skin Lesion Upload | pawnia-ai-2 | P2 | 1 |
| 5 | Safety Layer Integration — Contraindication Check | pawnia-ai-3 | P2 | 1 |
| 6 | Learning Loop Dashboard — Feedback to Retrain ML | pawnia-ml-2 | P2 | 1 |
| 7 | Integration Endpoint Tests | pawnia-ai-1 | P1 | 3, 4, 5, 6 |
| 8 | Architect Batch Review — Sprint 4 | architect | P1 | 7 |

### Dependency Graph
```
t_d5a4adfd (Data Model Alignment) — backend
  ├── t_04911e8e (Alembic Migration) — backend
  │     └── t_8ddfa6dc (Integration Enhancement) — backend
  │           └── t_7acd7d84 (Integration Tests) — pawnia-ai-1
  ├── t_9402ffee (Vision Analysis) — pawnia-ai-2 [P2]
  │     └── t_7acd7d84 (Integration Tests)
  ├── t_580075de (Safety Layer) — pawnia-ai-3 [P2]
  │     └── t_7acd7d84 (Integration Tests)
  └── t_36c22cc4 (Learning Loop) — pawnia-ml-2 [P2]
        └── t_7acd7d84 (Integration Tests)
              └── t_11b2c39f (Architect Review) — architect
```

### Key Decisions
- P1 tasks (Data Model, Migration, Integration Enhancement, Tests, Architect Review) harus selesai dulu sebelum deploy
- P2 tasks (Vision, Safety, Learning Loop) bisa parallel dengan P1 setelah Data Model selesai
- Architect review sebagai gate terakhir sebelum deploy ke VPS
- Integration Tests mencakup semua endpoint Sprint 4

### Files Updated
- `/home/ubuntu/sobatpaws/.hermes/STATUS.md` — Sprint 4 status updated

---

## ⏭️ Next Steps (Untuk Agent Selanjutnya)

1. **backend** — Mulai Data Model Alignment (Pet: color, microchip; User: first_name, last_name, address, avatar_url, date_of_birth)
2. **backend** — Lanjut Alembic Migration setelah data model selesai
3. **backend** — Integration Enhancement setelah migration
4. **pawnia-ai-2** — Vision Analysis for Admin (parallel, P2)
5. **pawnia-ai-3** — Safety Layer Integration (parallel, P2)
6. **pawnia-ml-2** — Learning Loop Dashboard (parallel, P2)
7. **pawnia-ai-1** — Integration Tests setelah implementation tasks selesai
8. **architect** — Batch Review sebagai gate terakhir
9. **devops** — Deploy setelah architect approve
