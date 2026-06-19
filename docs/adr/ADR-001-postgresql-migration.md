# ADR-001: PostgreSQL Migration for Sobatpaws Platform

## Status
Proposed

## Context
Saat ini Sobatpaws berjalan dengan:
1.  In-memory KnowledgeBase dari file JSON
2.  SQLite sebagai backend sementara untuk development
3.  JSONL files untuk learning loop log

Kebutuhan saat ini:
-   Konsistensi data transaksional untuk konsultasi klinis
-   ACID compliance untuk learning loop dan model registry
-   Concurrency untuk banyak dokter hewan online bersamaan
-   Foreign key constraint untuk integritas data klinis
-   Full text search untuk gejala dan penyakit
-   Query kompleks untuk ML view dan analitik

Alternatif yang dipertimbangkan:
- ✅ PostgreSQL 16
- ❌ SQLite (production tidak cocok untuk write concurrency)
- ❌ MongoDB (tidak perlu dokument oriented, schema ketat diperlukan untuk klinis)
- ❌ MySQL / MariaDB (kurang support untuk tipe JSONB, CTE recursive, dan window function)

## Decision
Migrasikan seluruh persistence layer ke **PostgreSQL 16**:
1.  Learning loop (konsultasi, doctor input, gold labels)
2.  Model registry dan lineage tracking
3.  Operational data: klinik, dokter, pemilik, hewan
4.  Reference data: taxonomy, penyakit, gejala (seed dari JSON curated)
5.  ML views materialized

Schema sudah didefinisikan di `dbml/schema.dbml` dan akan digenerate ke DDL PostgreSQL secara otomatis.

## Consequences

### Positif
-   ACID compliance untuk semua operasi klinis
-   Dukungan JSONB untuk data semi terstruktur
-   Full text search built-in
-   Transaction isolation untuk konsultasi paralel
-   Ready untuk scaling horizontal read replica
-   Tooling matang untuk backup, monitoring, dan migration

### Negatif
-   Perlu setup migrasi database (alembic)
-   Perlu perubahan pada `data_loader.py` untuk fall back ke JSON ketika DB tidak tersedia
-   Menambah dependency infrastruktur
-   Local development membutuhkan PostgreSQL server (via Docker)

### Risiko
-   Schema migration harus backward compatible
-   Seed generator harus dapat dijalankan berulang tanpa duplikat
-   Performance indexing untuk query ML yang kompleks

## Next Steps
1.  Setup alembic migration
2.  Implementasikan `model_registry_pg.py`
3.  Update `SOBATPAWS_LEARNING_BACKEND=postgres`
4.  Docker compose untuk local PostgreSQL
5.  Github Actions test pipeline dengan Postgres service
