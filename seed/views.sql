-- PostgreSQL Views untuk mengekstrak field dari JSONB document store
-- Memudahkan query dan reporting tanpa mengubah implementasi JSONB-first
-- Jalankan setelah schema.sql dan learning.sql:
--   psql "$DATABASE_URL" -f seed/views.sql

-- ============================================================================
-- VIEW: v_ai_conversations
-- Mengekstrak konsultasi dari learning_events (kind='consultation')
-- Mirip dengan tabel ai_conversations di schema.dbml
-- ============================================================================
CREATE OR REPLACE VIEW v_ai_conversations AS
SELECT
  le.id AS event_id,
  le.consultation_id,
  le.recorded_at AS started_at,
  -- Field dari context JSONB
  (le.payload->'context'->>'org_id')::bigint AS org_id,
  (le.payload->'context'->>'user_id')::bigint AS user_id,
  (le.payload->'context'->>'vet_id')::bigint AS vet_id,
  (le.payload->'context'->>'doctor_id')::bigint AS doctor_id,
  (le.payload->'context'->>'owner_id')::bigint AS owner_id,
  (le.payload->'context'->>'customer_id')::bigint AS customer_id,
  (le.payload->'context'->>'pet_id')::bigint AS pet_id,
  (le.payload->'context'->>'case_id')::bigint AS case_id,
  le.payload->'context'->>'external_consultation_id' AS external_consultation_id,
  le.payload->'context'->>'category_slug' AS category_slug,
  le.payload->'context'->>'breed_slug' AS breed_slug,
  (le.payload->'context'->>'age_years')::decimal(6,2) AS age_years,
  (le.payload->'context'->>'weight_kg')::decimal(6,2) AS weight_kg,
  le.payload->'context'->>'sex' AS sex,
  (le.payload->'context'->>'is_neutered')::boolean AS is_neutered,
  -- Judul otomatis dari kategori
  CASE
    WHEN le.payload->'context'->>'category_slug' IS NOT NULL
    THEN 'Konsultasi ' || INITCAP(REPLACE(le.payload->'context'->>'category_slug', '-', ' '))
    ELSE 'Konsultasi Baru'
  END AS title,
  -- Raw payload untuk akses lengkap
  le.payload AS full_payload
FROM learning_events le
WHERE le.kind = 'consultation'
ORDER BY le.recorded_at DESC;

COMMENT ON VIEW v_ai_conversations IS
  'View konsultasi dari learning_events JSONB. Menyamakan konsep ai_conversations tanpa FK wajib. '
  'Field diekstrak dari payload->context.';

-- ============================================================================
-- VIEW: v_ai_suggestions
-- Mengekstrak saran AI dari learning_events (kind='suggestion')
-- Mirip dengan tabel ai_suggestions di schema.dbml
-- ============================================================================
CREATE OR REPLACE VIEW v_ai_suggestions AS
SELECT
  le.id AS event_id,
  le.consultation_id,
  le.recorded_at AS created_at,
  -- Field dari suggestion JSONB
  le.payload->'suggestion'->>'suggestion_type' AS suggestion_type,
  le.payload->'suggestion'->>'summary' AS summary,
  le.payload->'suggestion'->'suggested_diseases' AS suggested_diseases,
  le.payload->'suggestion'->'suggested_diagnostics' AS suggested_diagnostics,
  le.payload->'suggestion'->'suggested_treatments' AS suggested_treatments,
  le.payload->'suggestion'->'suggested_products' AS suggested_products,
  le.payload->'suggestion'->'red_flags' AS red_flags,
  le.payload->'suggestion'->'safety_warnings' AS safety_warnings,
  (le.payload->'suggestion'->>'is_emergency')::boolean AS is_emergency,
  le.payload->'suggestion'->>'generated_by' AS generated_by,
  le.payload->'suggestion'->>'disclaimer' AS disclaimer,
  -- Penyakit teratas (untuk query cepat)
  (le.payload->'suggestion'->'suggested_diseases'->0->>'disease_slug') AS top_disease_slug,
  (le.payload->'suggestion'->'suggested_diseases'->0->>'name_id') AS top_disease_name,
  (le.payload->'suggestion'->'suggested_diseases'->0->>'confidence')::decimal(5,4) AS top_confidence,
  -- Raw payload
  le.payload AS full_payload
FROM learning_events le
WHERE le.kind = 'suggestion'
ORDER BY le.recorded_at DESC;

COMMENT ON VIEW v_ai_suggestions IS
  'View saran AI dari learning_events JSONB. Menyamakan konsep ai_suggestions tanpa FK wajib. '
  'Termasuk top_disease_* untuk query cepat oleh ML/reporting.';

-- ============================================================================
-- VIEW: v_ml_feedback
-- Mengekstrak feedback dokter dari learning_events (kind='feedback')
-- Mirip dengan tabel ml_feedback di schema.dbml
-- ============================================================================
CREATE OR REPLACE VIEW v_ml_feedback AS
SELECT
  le.id AS event_id,
  le.consultation_id,
  le.recorded_at AS created_at,
  -- Field dari feedback JSONB
  le.payload->>'suggestion_ref' AS suggestion_ref,
  le.payload->>'verdict' AS verdict,
  le.payload->>'corrected_disease_slug' AS corrected_disease_slug,
  le.payload->>'comment' AS comment,
  (le.payload->>'reviewer_id')::bigint AS reviewer_id,
  -- Mapping ke enum feedback_verdict untuk kompatibilitas
  CASE le.payload->>'verdict'
    WHEN 'correct' THEN 'correct'::feedback_verdict
    WHEN 'partially_correct' THEN 'partially_correct'::feedback_verdict
    WHEN 'incorrect' THEN 'incorrect'::feedback_verdict
    WHEN 'not_applicable' THEN 'not_applicable'::feedback_verdict
    ELSE NULL
  END AS verdict_enum,
  -- Raw payload
  le.payload AS full_payload
FROM learning_events le
WHERE le.kind = 'feedback'
ORDER BY le.recorded_at DESC;

COMMENT ON VIEW v_ml_feedback IS
  'View feedback dokter dari learning_events JSONB. Menyamakan konsep ml_feedback. '
  'Verdict: correct | partially_correct | incorrect | not_applicable. '
  'Ini adalah human-in-the-loop gold labels untuk retraining ML.';

-- ============================================================================
-- VIEW: v_ml_doctor_inputs
-- Mengekstrak input dokter dari learning_events (kind='doctor_input')
-- Gold labels untuk ML training
-- ============================================================================
CREATE OR REPLACE VIEW v_ml_doctor_inputs AS
SELECT
  le.id AS event_id,
  le.consultation_id,
  le.recorded_at AS created_at,
  -- Field dari doctor_input JSONB
  (le.payload->>'case_id')::bigint AS case_id,
  (le.payload->>'vet_id')::bigint AS vet_id,
  (le.payload->>'org_id')::bigint AS org_id,
  (le.payload->>'owner_id')::bigint AS owner_id,
  (le.payload->>'customer_id')::bigint AS customer_id,
  (le.payload->>'pet_id')::bigint AS pet_id,
  le.payload->>'external_consultation_id' AS external_consultation_id,
  -- Diagnosa dan gejala (gold labels utama)
  le.payload->>'confirmed_disease_slug' AS confirmed_disease_slug,
  le.payload->'differential_disease_slugs' AS differential_disease_slugs,
  le.payload->'confirmed_symptoms' AS confirmed_symptoms,
  -- Catatan klinis
  le.payload->>'clinical_notes' AS clinical_notes,
  le.payload->>'outcome' AS outcome,
  (le.payload->>'confidence')::decimal(5,2) AS confidence,
  -- Tindakan dan resep
  le.payload->'diagnostics_ordered' AS diagnostics_ordered,
  le.payload->'treatments_given' AS treatments_given,
  le.payload->'products_prescribed' AS products_prescribed,
  -- Raw payload
  le.payload AS full_payload
FROM learning_events le
WHERE le.kind = 'doctor_input'
ORDER BY le.recorded_at DESC;

COMMENT ON VIEW v_ml_doctor_inputs IS
  'View input dokter (gold labels) dari learning_events JSONB. '
  'confirmed_disease_slug + confirmed_symptoms adalah label emas untuk retraining ML. '
  'Digunakan oleh learning_store.export_clinical_rows() untuk membangun dataset training.';

-- ============================================================================
-- VIEW: v_learning_events_summary
-- Ringkasan semua event untuk dashboard
-- ============================================================================
CREATE OR REPLACE VIEW v_learning_events_summary AS
SELECT
  le.kind,
  COUNT(*) AS event_count,
  MIN(le.recorded_at) AS earliest_at,
  MAX(le.recorded_at) AS latest_at,
  COUNT(DISTINCT le.consultation_id) AS unique_consultations
FROM learning_events le
GROUP BY le.kind
ORDER BY event_count DESC;

COMMENT ON VIEW v_learning_events_summary IS
  'Ringkasan agregat learning_events untuk dashboard dan monitoring.';

-- ============================================================================
-- VIEW: v_consultations_with_suggestions
-- Join konsultasi dengan saran AI terbaru (untuk reporting)
-- ============================================================================
CREATE OR REPLACE VIEW v_consultations_with_suggestions AS
WITH latest_suggestions AS (
  SELECT
    s.consultation_id,
    s.summary,
    s.top_disease_slug,
    s.top_disease_name,
    s.top_confidence,
    s.is_emergency,
    s.created_at AS suggestion_at,
    ROW_NUMBER() OVER (
      PARTITION BY s.consultation_id
      ORDER BY s.created_at DESC
    ) AS rn
  FROM v_ai_suggestions s
),
latest_feedback AS (
  SELECT
    f.consultation_id,
    f.verdict,
    f.comment AS feedback_comment,
    f.created_at AS feedback_at,
    ROW_NUMBER() OVER (
      PARTITION BY f.consultation_id
      ORDER BY f.created_at DESC
    ) AS rn
  FROM v_ml_feedback f
),
latest_doctor_input AS (
  SELECT
    d.consultation_id,
    d.confirmed_disease_slug,
    d.confirmed_symptoms,
    d.clinical_notes,
    d.created_at AS doctor_input_at,
    ROW_NUMBER() OVER (
      PARTITION BY d.consultation_id
      ORDER BY d.created_at DESC
    ) AS rn
  FROM v_ml_doctor_inputs d
)
SELECT
  c.consultation_id,
  c.started_at,
  c.category_slug,
  c.breed_slug,
  c.age_years,
  c.weight_kg,
  c.pet_id,
  c.vet_id,
  c.case_id,
  c.external_consultation_id,
  -- Suggestion terbaru
  s.summary AS ai_summary,
  s.top_disease_slug AS ai_top_disease,
  s.top_disease_name AS ai_top_disease_name,
  s.top_confidence AS ai_confidence,
  s.is_emergency AS ai_is_emergency,
  s.suggestion_at,
  -- Feedback
  f.verdict AS feedback_verdict,
  f.feedback_comment,
  f.feedback_at,
  -- Doctor input (gold label)
  d.confirmed_disease_slug AS doctor_diagnosis,
  d.confirmed_symptoms AS doctor_symptoms,
  d.clinical_notes,
  -- Status: apakah ada koreksi dokter?
  CASE
    WHEN d.confirmed_disease_slug IS NOT NULL
     AND s.top_disease_slug IS NOT NULL
     AND d.confirmed_disease_slug != s.top_disease_slug
    THEN 'corrected'
    WHEN d.confirmed_disease_slug IS NOT NULL THEN 'confirmed'
    WHEN f.verdict IS NOT NULL THEN 'reviewed'
    ELSE 'pending'
  END AS review_status
FROM v_ai_conversations c
LEFT JOIN latest_suggestions s ON s.consultation_id = c.consultation_id AND s.rn = 1
LEFT JOIN latest_feedback f ON f.consultation_id = c.consultation_id AND f.rn = 1
LEFT JOIN latest_doctor_input d ON d.consultation_id = c.consultation_id AND d.rn = 1
ORDER BY c.started_at DESC;

COMMENT ON VIEW v_consultations_with_suggestions IS
  'Denormalized view untuk reporting dan analisis performa AI. '
  'Menggabungkan konsultasi + saran AI + feedback + diagnosa dokter. '
  'review_status: pending | reviewed | confirmed | corrected.';

-- ============================================================================
-- Index tambahan untuk performa query pada JSONB field
-- ============================================================================
-- Index untuk query berdasarkan category_slug
CREATE INDEX IF NOT EXISTS idx_learning_events_payload_category
  ON learning_events ((payload->'context'->>'category_slug'))
  WHERE kind = 'consultation';

-- Index untuk query berdasarkan vet_id
CREATE INDEX IF NOT EXISTS idx_learning_events_payload_vet
  ON learning_events (((payload->'context'->>'vet_id')::bigint))
  WHERE kind = 'consultation';

-- Index untuk query berdasarkan pet_id
CREATE INDEX IF NOT EXISTS idx_learning_events_payload_pet
  ON learning_events (((payload->'context'->>'pet_id')::bigint))
  WHERE kind = 'consultation';

-- Index untuk query berdasarkan verdict
CREATE INDEX IF NOT EXISTS idx_learning_events_payload_verdict
  ON learning_events ((payload->>'verdict'))
  WHERE kind = 'feedback';

-- Index untuk query berdasarkan confirmed_disease_slug
CREATE INDEX IF NOT EXISTS idx_learning_events_payload_disease
  ON learning_events ((payload->>'confirmed_disease_slug'))
  WHERE kind = 'doctor_input';
