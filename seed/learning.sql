-- Tabel append-only untuk jejak konsultasi & pembelajaran (di luar FK ketat DBML).
-- Mirror struktur JSONL di artifacts/learning/*.jsonl agar bisa query & backup di PostgreSQL.
-- Jalankan setelah schema.sql:
--   psql "$DATABASE_URL" -f seed/learning.sql

CREATE TABLE IF NOT EXISTS learning_events (
  id              TEXT PRIMARY KEY,
  consultation_id TEXT NOT NULL,
  kind            TEXT NOT NULL,  -- consultation | intake | suggestion | doctor_input | feedback
  payload         JSONB NOT NULL,
  recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_learning_events_consultation
  ON learning_events (consultation_id);

CREATE INDEX IF NOT EXISTS idx_learning_events_kind
  ON learning_events (kind);

CREATE INDEX IF NOT EXISTS idx_learning_events_recorded
  ON learning_events (recorded_at DESC);

COMMENT ON TABLE learning_events IS
  'Jejak konsultasi AI + input dokter untuk human-in-the-loop retraining. '
  'Selaras konsep tabel ai_conversations / ai_suggestions / ml_feedback tanpa FK wajib.';
