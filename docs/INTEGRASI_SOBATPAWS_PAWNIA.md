# Panduan Integrasi: Sobatpaws AI + Pawnia AI - sobat-paws Ecosystem

**Versi:** 1.0.0 | **Tanggal:** 28 Juni 2026 | **Oleh:** Wins (PM, Naincode AI Dept)

---

## 1. Arsitektur Overview

```
sobat-paws ORG (GitHub)
  sobatpaws-admin (React, Port 3333)
  sobatpaws-mobile (Flutter/Swift)
          |
          v
  Ekosistem Satwa API (43.129.56.221:8080)
    AI Gateway - POST /api/v1/ai/chat
    Integration API - /api/v1/integration/*
    EMR Service - /api/v1/emr/*
    Pawnia Orchestrator - 9 AI Agents
    PostgreSQL - sobatpaws-db (healthy)
```

## 2. Endpoint yang Tersedia (9 Integration Endpoints)

**Public:**
- GET /health - Health check
- GET /api/v1/integration/health - Integration health

**Requires Auth (JWT atau API Key):**
| Endpoint | Fungsi |
|----------|--------|
| POST /api/v1/integration/appointment/screening | AI Pre-Screening |
| GET /api/v1/integration/customer/{id}/medical-history | Riwayat medis |
| POST /api/v1/integration/product/recommend | Rekomendasi produk |
| GET /api/v1/integration/dashboard/insights | AI Insights |
| POST /api/v1/integration/vision/skin-lesion | Analisis lesi kulit |
| POST /api/v1/integration/safety/check-contraindication | Cek kontraindikasi obat |
| GET /api/v1/integration/learning-loop/stats | Stats feedback |
| POST /api/v1/integration/learning-loop/trigger-retrain | Trigger retrain ML |

**AI Gateway:** POST /api/v1/ai/chat, GET /api/v1/ai/status, POST /api/v1/ai/feedback
**EMR Service:** GET /api/v1/pets/{id}/context, GET /api/v1/pets/{id}/consultations

## 3. Autentikasi

- API Key: Header X-EkosistemSatwa-Key
- JWT Bearer: Header Authorization: Bearer
- Dapatkan JWT: POST /api/v1/auth/login
- Role: public, vet, admin (sesuai akses endpoint)

## 4. Integrasi Admin Panel (4 Langkah)

**Langkah 1: CONNECT**
- Set env: NEXT_PUBLIC_EKOSISTEM_SATWA_API=http://43.129.56.221:8080
- Test: curl http://43.129.56.221:8080/health

**Langkah 2: AI PRE-SCREENING DI APPOINTMENT**
- POST /api/v1/integration/appointment/screening
- Input: species, breed, age_years, symptoms[]
- Output: risk_level (low/medium/high/critical), risk_score, urgency
- Integrasikan ke: appointment form, detail appointment

**Langkah 3: MEDICAL HISTORY**
- GET /api/v1/integration/customer/{external_id}/medical-history
- Output: pets info, vaccinations, medications, consultations
- Integrasikan ke: customer detail page

**Langkah 4: DASHBOARD INSIGHTS**
- GET /api/v1/integration/dashboard/insights
- Output: species_distribution, breed_risk_profiles, disease_trends
- Integrasikan ke: dashboard admin

## 5. Integrasi Mobile App

POST /api/v1/ai/chat
Body: { message, session_id, pet_context: { species, breed, age_years, weight_kg } }
Response: { suggestion: { text, risk_level, risk_score, recommendation }, agent }

HIGH RISK -> Emergency warning + clinic recommendation
MEDIUM RISK -> Rekomendasi appointment
LOW RISK -> Home care tips

## 6. Testing

curl -sf http://43.129.56.221:8080/health
curl -sf http://43.129.56.221:8080/api/v1/ai/status
curl -sf http://43.129.56.221:8080/api/v1/integration/health

## 7. Troubleshooting

404 - Rebuild: docker compose -f docker-compose.prod.yml build --no-cache api
401 - Cek auth header (JWT atau API Key)
Timeout - Set SOBATPAWS_AI_AUGMENTATION_MODE=smart

## 8. Status: 28 Juni 2026

- VPS: 43.129.56.221:8080 | API: 200 OK
- 9 Pawnia Agents: pet_companion, triage_emergency, vet_escalation, vision_screening,
  behavior_insight, behavior_fun, nutrition_advisor, meal_planner, medication_adherence
- 9 Integration Endpoints Live
- 10 species | 177 breeds | 44 diseases | 207 symptoms
- Sprint 4 (Admin Panel) DONE | Sprint 5 (Knowledge Expansion) RUNNING
- Docs: docs/INTEGRATION_ADMIN_PANEL.md, docs/ALIGNMENT_ANALYSIS.md
