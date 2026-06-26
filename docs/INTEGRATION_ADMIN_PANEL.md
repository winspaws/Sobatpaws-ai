# Analisis Integrasi: sobatpaws-admin -> Pawnia & Ekosistem Satwa

**Tanggal:** 27 Juni 2026
**Oleh:** Wins (PM)

---

## 1. Ringkasan sobatpaws-admin

**sobatpaws-admin** (alias `petpro-admin`) adalah **Admin Panel** untuk platform PetPro - marketplace layanan dan produk hewan peliharaan.

### Stack Teknis
| Komponen | Detail |
|----------|--------|
| Frontend | React 19 + TypeScript + Vite |
| Styling | Tailwind CSS + Headless UI + Heroicons |
| State | Zustand + TanStack React Query |
| HTTP | Axios (baseURL: http://localhost:3004/api/admin) |
| Routing | React Router v7 |
| Build | Docker multi-stage (Nginx) |
| Port | 3333:80 |

### Domain Bisnis (17 modul)

| Modul | Endpoint API | Status |
|-------|-------------|--------|
| Auth | /auth/* | Login, register, profile, change password, refresh token |
| Dashboard | /dashboard/* | Summary, vendor stats, sales, user growth, satisfaction trends |
| Vendors | /vendor/* | CRUD, KYC approve/reject, services, orders, reviews, ratings |
| Customers | /customer/* | List, detail, appointments |
| Appointments | /appointment/* | List, detail, cancel, reminder |
| Orders | /order/* | List, detail, print |
| Products | /product/* | List, detail, by shop |
| Finance | /finance/* | List, detail |
| Commission | /commission/* | Statements, withdrawals, requests |
| Payout | /payout/* | List |
| Withdraw | /withdraw/* | List |
| Employees | /employee/* | List |
| Settings | /settings/* | Users, security, systems, sessions |
| Audit Logs | /audit/* | Logs |
| Notifications | /notification/* | Notifications |
| Doctor List | /doctor/* | Doctor list |
| Vendor Profile | /vendor/profile/* | Profile management |

---

## 2. Gap Analysis

### Yang SUDAH Ada di sobatpaws-admin
- Manajemen vendor (clinic & petshop) - KYC, status, services
- Manajemen customer (pet owners)
- Manajemen appointment (booking system)
- Manajemen produk & inventory
- Manajemen order (POS & online)
- Manajemen dokter & staff
- Dashboard analytics (revenue, orders, customers, satisfaction)
- Finance & commission tracking
- Review & rating system

### Yang BELUM Ada (potensi integrasi dengan Ekosistem Satwa)

| Fitur | Ada di Admin? | Ada di ES? | Potensi |
|-------|:------------:|:----------:|---------|
| AI Consultation (Pawnia) | X | Yes (9 agents) | HIGH |
| EMR / Medical Records | X | Yes (13 models) | HIGH |
| AI Symptom Checker | X | Yes (ML + RAG) | HIGH |
| Vision Analysis | X | Yes (Vision API) | MEDIUM |
| Smart Reminder | X | Yes (Notification) | MEDIUM |
| Product Recommendation AI | X | Yes (Nutrition Advisor) | MEDIUM |
| Safety Guardrails | X | Yes (Safety Layer) | LOW |
| Learning Loop | X | Yes (Feedback) | LOW |

---

## 3. Rencana Integrasi - 3 Fase

### Fase 1: Quick Wins (Estimasi: 3-5 hari)

#### 1.1 AI Pre-Screening di Appointment Booking
**Integrasi:** Admin -> Ekosistem Satwa AI Gateway

**Flow:**
```
Customer booking appointment
    -> Admin panel collects: species, breed, age, symptoms (text)
    -> POST /api/v1/ai/chat -> Pawnia Orchestrator
    -> Response: risk_level, suggested_specialist, urgency
    -> Tampilkan di admin: "High Risk - Segera jadwalkan dokter"
```

**Perubahan di Admin:**
- Tambah field `symptoms` di appointment form
- Tambah widget `AI Pre-Screening` di detail appointment
- Tambah kolom `risk_level` di tabel appointment

**Endpoint Admin baru:**
```
POST /api/admin/appointment/{id}/ai-screening
```

#### 1.2 Pet Medical History View
**Integrasi:** Admin -> Ekosistem Satwa EMR Service

**Flow:**
```
Admin lihat detail customer
    -> GET /api/v1/pets/{pet_id}/context -> EMR Service
    -> Response: vaccinations, medications, EMR history
    -> Tampilkan di tab "Medical History" customer detail
```

**Perubahan di Admin:**
- Tambah tab `Medical History` di Customer Detail Page
- Tampilkan: vaksinasi, obat, riwayat konsultasi AI

**Endpoint Admin baru:**
```
GET /api/admin/customer/{id}/medical-history
```

### Fase 2: Deep Integration (Estimasi: 1-2 minggu)

#### 2.1 AI-Powered Dashboard Insights
**Integrasi:** Admin Dashboard -> ES ML + Knowledge Base

**Tambahan di Dashboard:**
- Species Distribution Chart - Dari KB Ekosistem Satwa
- Disease Trends - Penyakit paling umum per periode
- AI Suggestion Accuracy - Dari Learning Loop feedback
- Breed Risk Profile - Ras dengan risiko penyakit tinggi

#### 2.2 Smart Product Recommendations
**Integrasi:** Admin Product -> Pawnia Nutrition Advisor

**Flow:**
```
Admin lihat product inventory
    -> GET /api/v1/knowledge/query -> RAG Pipeline
    -> AI rekomendasi: "Produk ini cocok untuk diet obesitas kucing"
    -> Tampilkan di detail product
```

#### 2.3 Doctor-Vet Escalation Integration
**Integrasi:** Admin Doctor List -> Pawnia Vet Escalation Agent

**Flow:**
```
Pawnia deteksi perlu vet escalation
    -> GET /api/admin/doctor/list -> Ambil daftar dokter
    -> Rekomendasikan dokter spesialis ke user
```

### Fase 3: Advanced (Estimasi: 2-4 minggu)

#### 3.1 Vision Analysis for Admin
- Upload foto lesi kulit di admin panel
- Kirim ke /api/v1/vision/analyze
- Tampilkan hasil analisis AI

#### 3.2 Learning Loop Dashboard
- Tampilkan feedback dokter -> accuracy metrics
- Trigger retrain ML dari admin panel
- Model version comparison

#### 3.3 Safety Layer Integration
- Cek kontraindikasi obat saat admin input product
- Peringatan otomatis: "Obat ini fatal untuk kucing!"
- Integrasi dengan product_species_safety

---

## 4. Arsitektur Integrasi

```
+------------------------------------------------------------------+
|                    SOBATPAWS-ADMIN (React)                        |
|  Port 3333                                                       |
|  +----------+ +----------+ +----------+ +------------------+     |
|  | Dashboard| | Customer | | Appoint  | | Product          |     |
|  | (enhanced| | (med hist| | (AI pre- | | (AI recom)       |     |
|  |  + AI)   | |  + EMR)  | | screen)  | |                  |     |
|  +----------+ +----------+ +----------+ +------------------+     |
+----------------------+-------------------------------------------+
                       |
          +------------+------------+
          v            v            v
+-----------------+ +-----------------+ +----------------------+
|  Admin Backend   | |  Ekosistem      | |  Ekosistem Satwa    |
|  (existing)      | |  Satwa API      | |  AI Gateway         |
|  localhost:3004  | |  localhost:8080 | |  /api/v1/ai/chat    |
|  /api/admin/*    | |  /api/v1/*      | |  /api/v1/vision     |
+-----------------+ +-----------------+ +----------------------+
```

### Opsi Implementasi

**Opsi A: Admin Backend Proxy (Rekomendasi)**
- Admin backend (:3004) bertindak sebagai BFF
- Admin backend panggil ES API internal
- Admin frontend tetap panggil 1 backend (/api/admin)
- Pro: Security terpusat, no CORS issues, caching
- Con: Perlu modifikasi admin backend

**Opsi B: Direct from Frontend**
- Admin frontend panggil langsung ES API
- Pro: Cepat implementasi
- Con: CORS, API key exposure, no caching

---

## 5. Task Breakdown

| Task | Assignee | Depends On | Priority |
|------|----------|------------|----------|
| AI Pre-Screening Widget | pawnia-backend-3 | AI Gateway (t_3fd836ce) | P1 |
| Pet Medical History View | pawnia-backend-2 | EMR Sync (t_775a66c2) | P1 |
| Dashboard AI Insights | pawnia-ai-1 | Integration done | P2 |
| Product AI Recommendations | pawnia-ai-3 | RAG Pipeline | P2 |
| Doctor-Vet Escalation | pawnia-ai-1 | AI Gateway | P2 |
| Vision Analysis | pawnia-ai-2 | Vision API | P3 |
| Safety Layer | pawnia-ai-3 | Safety Layer | P3 |

---

## 6. API Contract

### 6.1 AI Pre-Screening
```http
POST /api/admin/appointment/{id}/ai-screening
Content-Type: application/json
Authorization: Bearer <admin_token>

{
  "species": "cat",
  "breed": "cat-persian",
  "age_years": 3,
  "symptoms": ["muntah", "lemas", "tidak mau makan"],
  "duration_days": 2
}
```

Response:
```json
{
  "success": true,
  "data": {
    "risk_level": "high",
    "risk_score": 65,
    "suggested_specialist": "dokter_hewan_umum",
    "urgency": "within_24h",
    "ai_summary": "Kucing menunjukkan gejala gastroenteritis...",
    "disclaimer": "Ini bukan diagnosis definitif..."
  }
}
```

### 6.2 Pet Medical History
```http
GET /api/admin/customer/{id}/medical-history?pet_id={pet_id}
```

Response:
```json
{
  "success": true,
  "data": {
    "pet": { "name": "Milo", "species": "cat", "breed": "persian" },
    "vaccinations": [
      { "name": "FVRCP", "date": "2026-01-15", "next_due": "2027-01-15" }
    ],
    "active_medications": [],
    "recent_consultations": [
      { "date": "2026-06-20", "risk_level": "low", "summary": "..." }
    ],
    "chronic_conditions": []
  }
}
```

---

## 7. Rekomendasi Prioritas

| Priority | Item | Effort | Impact | Depends On |
|----------|------|--------|--------|------------|
| P1 | AI Pre-Screening | 2 hari | Tinggi | AI Gateway (running) |
| P1 | Pet Medical History | 2 hari | Tinggi | EMR Sync (blocked) |
| P2 | Dashboard AI Insights | 3 hari | Sedang | Integration done |
| P2 | Product AI Recommendations | 2 hari | Sedang | RAG Pipeline |
| P3 | Vision Analysis | 3 hari | Rendah | Vision API |
| P3 | Safety Layer | 2 hari | Rendah | Safety Layer |

---

## 8. Kesimpulan

**sobatpaws-admin** adalah PetPro Admin Panel - platform marketplace untuk klinik hewan & petshop dengan 17 modul bisnis fungsional.

**Potensi integrasi dengan Ekosistem Satwa + Pawnia sangat tinggi**, terutama di 3 area:
1. **AI Pre-Screening** - Sebelum appointment, Pawnia bisa screening gejala
2. **Pet Medical History** - EMR Service melengkapi data customer
3. **Dashboard Insights** - ML + Knowledge Base enrich analytics

**Rekomendasi:** Mulai Fase 1 (Quick Wins) segera setelah AI Gateway Integration selesai deploy.
