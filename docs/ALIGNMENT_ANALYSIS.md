# Alignment Analysis: Ekosistem Satwa <-> sobatpaws-admin

**Tanggal:** 27 Juni 2026
**Oleh:** Wins (PM)

---

## 1. Ringkasan Alignment

### sobatpaws-admin (PetPro Admin Panel)
- **Tujuan:** Admin panel marketplace klinik hewan & petshop
- **Stack:** React 19 + TypeScript + Vite + Tailwind
- **Backend:** localhost:3004/api/admin (Express/Fastify)
- **Auth:** JWT + refresh token, cookie-based (withCredentials: true)
- **Database:** PostgreSQL (managed by admin backend)

### Ekosistem Satwa (Our Backend)
- **Tujuan:** AI Services + EMR + Knowledge Base untuk veterinary
- **Stack:** FastAPI + SQLAlchemy + PostgreSQL
- **Port:** 8080:8000 (Docker)
- **Auth:** API Key-based (X-API-Key, X-EkosistemSatwa-Key)
- **Database:** PostgreSQL (sobatpaws-db)

### Alignment Score: 7/10
Kita sudah 70% aligned. Ada 3 gap utama yang perlu ditutup.

---

## 2. Gap Analysis Detail

### 2.1 Auth System
| Aspek | sobatpaws-admin | Ekosistem Satwa | Gap |
|-------|----------------|-----------------|-----|
| Method | JWT + Refresh Token (cookie) | API Key (header) | BERBEDA |
| Credentials | withCredentials: true | X-API-Key header | BERBEDA |
| Session | Token-based, auto-refresh | Static key | BERBEDA |
| User model | id, email, firstName, lastName, role, status | id, external_id, name, email, phone, role | MINOR |

**Action:** Tambah JWT auth middleware di ES API agar kompatibel dengan admin panel.

### 2.2 ID Schema
| Aspek | sobatpaws-admin | Ekosistem Satwa | Gap |
|-------|----------------|-----------------|-----|
| ID type | string (UUID) | integer (auto-increment) | BERBEDA |
| External ID | Tidak ada | Ada `external_id` field | OK |
| Pet ID | string UUID | integer | BERBEDA |

**Action:** ES sudah punya `external_id` — ini cukup untuk mapping. Admin cukup kirim `external_id` saat create data.

### 2.3 Pet Model
| Field | sobatpaws-admin (`AppointmentPet`) | Ekosistem Satwa (`Pet`) | Match? |
|-------|-----------------------------------|------------------------|--------|
| id | string | int | OK (external_id) |
| name | string | name | OK |
| species | string (opsional) | species (wajib) | OK |
| breed | string | breed (opsional) | OK |
| color | string | TIDAK ADA | ❌ |
| photo_url | string (opsional) | photo_url (opsional) | OK |
| type | string (null) | - | Alias species |

**Action:** Tambah field `color` ke Pet model.

### 2.4 Customer Model
| Field | sobatpaws-admin (`CustomerListItem`) | Ekosistem Satwa (`User`) | Match? |
|-------|--------------------------------------|--------------------------|--------|
| id | string | int | OK (external_id) |
| first_name | string | name (full) | MINOR |
| last_name | string | name (full) | MINOR |
| email | string | email | OK |
| phone_number | string | phone | OK |
| address | object | TIDAK ADA | ❌ |
| avatar_url | string | TIDAK ADA | ❌ |
| role | string | role | OK |
| date_of_birth | string | TIDAK ADA | ❌ |

**Action:** Tambah field `first_name`, `last_name`, `address`, `avatar_url`, `date_of_birth` ke User model.

### 2.5 Appointment Model
| Field | sobatpaws-admin | Ekosistem Satwa | Match? |
|-------|----------------|-----------------|--------|
| Booking & scheduling | ✅ Full CRUD | ❌ Tidak ada | ❌ |
| Status tracking | ✅ pending/confirmed/completed/cancelled | ❌ | ❌ |
| Payment status | ✅ | ❌ | ❌ |
| AI pre-screening | ❌ | ✅ Bisa integrasi | 🎯 |

**Action:** ES tidak perlu duplicate appointment system. Cukup sediakan endpoint AI pre-screening yang bisa dipanggil admin panel.

### 2.6 Vendor/Clinic Model
| Field | sobatpaws-admin (`VendorDetail`) | Ekosistem Satwa | Match? |
|-------|----------------------------------|-----------------|--------|
| Business name | ✅ | ❌ Tidak ada | ❌ |
| KYC status | ✅ approved/submitted/rejected | ❌ | ❌ |
| Services | ✅ CRUD | ❌ | ❌ |
| Employees/Staff | ✅ | ❌ | ❌ |
| Operating hours | ✅ | ❌ | ❌ |
| Veterinarian license | ✅ | ❌ | ❌ |

**Action:** ES tidak perlu duplicate vendor management. Cukup sediakan endpoint yang bisa diquery oleh admin panel.

### 2.7 Product Model
| Field | sobatpaws-admin | Ekosistem Satwa | Match? |
|-------|----------------|-----------------|--------|
| Product CRUD | ✅ Full | ❌ Tidak ada | ❌ |
| Inventory | ✅ Multi-warehouse | ❌ | ❌ |
| Pricing | ✅ Multiple price types | ❌ | ❌ |
| AI Recommendations | ❌ | ✅ Bisa integrasi | 🎯 |

**Action:** ES sediakan endpoint product recommendation via RAG + Knowledge Base.

---

## 3. Alignment Score per Domain

| Domain | Score | Status |
|--------|:----:|--------|
| Auth System | 4/10 | ❌ Perlu JWT middleware |
| ID Schema | 8/10 | ✅ external_id covers it |
| Pet Model | 7/10 | ⚠️ Tambah color field |
| Customer/User | 5/10 | ⚠️ Tambah address, avatar, split name |
| Appointment | 3/10 | ❌ ES tidak manage appointment |
| Vendor/Clinic | 2/10 | ❌ ES tidak manage vendor |
| Product | 2/10 | ❌ ES tidak manage product |
| AI Services | 10/10 | ✅ Core strength ES |
| EMR/Medical | 9/10 | ✅ Almost complete |
| Knowledge Base | 9/10 | ✅ Almost complete |

**Overall: 6.5/10**

---

## 4. Action Items: Adjustments Needed

### Priority 1: API Compatibility (Harus dilakukan)

#### 4.1 Tambah JWT Auth Middleware
**File:** `src/ekosistem_satwa/api/auth.py`

Tambah support untuk JWT Bearer token selain API Key:
```python
# Existing: X-API-Key, X-EkosistemSatwa-Key
# New: Authorization: Bearer <jwt_token>
# New: Cookie-based session
```

**Endpoint baru:**
```
POST /api/v1/auth/login       # Login, return JWT
POST /api/v1/auth/refresh     # Refresh token
GET  /api/v1/auth/profile     # Get current user profile
```

#### 4.2 Tambah CORS Support untuk Admin Panel
**File:** `src/ekosistem_satwa/api/main.py`

Admin panel origin: `http://localhost:3333` (dev), `https://admin.sobatpaws.com` (prod)

#### 4.3 Standardisasi Response Format
Admin panel expects:
```json
{
  "success": true,
  "data": {...},
  "pagination": {...}
}
```

ES saat ini menggunakan format sendiri. Perlu wrapper.

### Priority 2: Data Model Alignment

#### 4.4 Perbaiki User Model
**File:** `src/ekosistem_satwa/emr/models.py`

Tambah:
- `first_name`, `last_name` (split from `name`)
- `address` (JSONB)
- `avatar_url`
- `date_of_birth`

#### 4.5 Perbaiki Pet Model
**File:** `src/ekosistem_satwa/emr/models.py`

Tambah:
- `color` field

### Priority 3: Integration Endpoints (Baru)

#### 4.6 AI Pre-Screening Endpoint
**File:** `src/ekosistem_satwa/api/integration_router.py`

```http
POST /api/v1/integration/appointment/screening
Body: { species, breed, age, symptoms, duration }
Response: { risk_level, risk_score, suggested_specialist, urgency, ai_summary }
```

#### 4.7 Product Recommendation Endpoint
```http
POST /api/v1/integration/product/recommend
Body: { species, breed, age, condition }
Response: { recommendations: [{ product_name, category, reason }] }
```

#### 4.8 Customer Medical History Endpoint
```http
GET /api/v1/integration/customer/{external_id}/medical-history
Response: { pets: [{ name, species, vaccinations, medications, consultations }] }
```

---

## 5. Rencana Implementasi

### Fase 1: API Compatibility (2-3 hari)
| Task | File | Assignee |
|------|------|----------|
| JWT auth middleware | `src/ekosistem_satwa/api/auth.py` | backend |
| Login/refresh/profile endpoints | `src/ekosistem_satwa/api/auth_router.py` | backend |
| CORS config update | `src/ekosistem_satwa/api/main.py` | backend |
| Response format standardization | `src/ekosistem_satwa/api/deps.py` | backend |

### Fase 2: Data Model Update (1-2 hari)
| Task | File | Assignee |
|------|------|----------|
| Add first_name, last_name, address to User | `src/ekosistem_satwa/emr/models.py` | backend |
| Add color to Pet | `src/ekosistem_satwa/emr/models.py` | backend |
| Migration scripts | `alembic/versions/` | backend |

### Fase 3: Integration Endpoints (2-3 hari)
| Task | File | Assignee |
|------|------|----------|
| AI Pre-Screening endpoint | `src/ekosistem_satwa/api/integration_router.py` | pawnia-ai-1 |
| Product Recommendation endpoint | `src/ekosistem_satwa/api/integration_router.py` | pawnia-ai-3 |
| Customer Medical History endpoint | `src/ekosistem_satwa/api/integration_router.py` | pawnia-backend-2 |

---

## 6. Kesimpulan

**Ekosistem Satwa sudah dibangun dengan arsitektur yang tepat untuk diintegrasikan dengan sobatpaws-admin.** 

Kekuatan utama kita:
- ✅ AI Orchestrator (Pawnia) — 9 agents siap pakai
- ✅ EMR Service — 13 medical models
- ✅ RAG Pipeline — Knowledge retrieval
- ✅ Safety Layer — Guardrails
- ✅ Vision Analysis — Image processing

Yang perlu disesuaikan:
1. 🔧 **Auth system** — Tambah JWT support (P1)
2. 🔧 **Data models** — Tambah field yang missing (P2)
3. 🔧 **Integration endpoints** — Endpoint spesifik untuk admin panel (P3)

**Rekomendasi:** Mulai Fase 1 segera setelah `t_3fd836ce` (Integration & VPS Deploy) selesai.
