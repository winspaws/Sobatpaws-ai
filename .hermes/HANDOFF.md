# Sobatpaws Telekonsultasi Frontend — HANDOFF

> Tanggal: 2025-06-19
> Profile: frontend
> Task: t_cbf658a7

---

## ✅ Apa yang Dibangun

### 1. Halaman Telekonsultasi (`web/telekonsultasi.html`)

Single-page application (SPA) untuk frontend telekonsultasi dengan fitur:

#### 📋 Intake Form (3-step wizard)
- **Step 1: Informasi Hewan**
  - Spesies (dropdown dari `GET /categories`)
  - Ras (dropdown dari `GET /categories/{slug}/breeds`)
  - Umur (tahun), Berat (kg)
  - Jenis kelamin, Status sterilisasi

- **Step 2: Gejala**
  - Keluhan/riwayat (textarea)
  - Chip gejala umum (click-to-toggle)
  - Mendukung multiple selection

- **Step 3: Review**
  - Ringkasan seluruh input
  - Tombol "Mulai Konsultasi"

#### 💬 Chat Interface
- Layout sidebar (intake) + main (chat)
- Responsive (mobile: stacked, desktop: side-by-side)
- Message bubbles dengan avatar:
  - User (kanan, biru gradient)
  - AI (kiri, panel background)
  - System (tengah, muted)

#### 🧠 AI Suggestion Cards
Setiap response AI menampilkan:
- **Emergency banner** (jika `is_emergency=true`)
- **Summary box** (ringkasan saran)
- **Red flags** (jika ada)
- **Diagnosa potensial** dengan confidence bar
- **Pemeriksaan disarankan**
- **Tindakan & Produk**
- **Pertanyaan lanjutan**
- **Disclaimer** standar

#### 📹 Video Call Placeholder
- Panel terpisah di atas chat
- Toggle button di header
- Placeholder untuk integrasi WebRTC nanti
- Controls: Mic, Camera, Hubungkan, Tutup

---

## 🔌 API Integration

### Endpoint yang Digunakan

| Method | Endpoint | Kegunaan |
|--------|----------|----------|
| `GET` | `/categories` | Load daftar spesies |
| `GET` | `/categories/{slug}/breeds` | Load ras per spesies |
| `POST` | `/consultations` | Mulai konsultasi baru |
| `POST` | `/consultations/{id}/turns` | Tambah pesan/giliran |
| `GET` | `/api/stats/breakdown` | Stats untuk gejala |

### Request/Response Contract

#### Start Consultation (`POST /consultations`)
```json
{
  "context": {
    "category_slug": "cat",
    "breed_slug": "cat-persian",
    "age_years": 3.5,
    "weight_kg": 4.2,
    "sex": "male",
    "is_neutered": true,
    "vet_id": 1,
    "owner_id": 1,
    "pet_id": 1
  },
  "intake": {
    "channel": "chat",
    "text": "Kucing muntah dan tidak mau makan",
    "is_first_contact": true
  }
}
```

#### Response (`ConsultationResponse`)
```json
{
  "consultation_id": "uuid-xxx",
  "intake": {
    "complaint_text": "...",
    "symptoms": [...]
  },
  "suggestion": {
    "summary": "...",
    "is_emergency": false,
    "suggested_diseases": [
      {"disease_slug": "...", "name_id": "...", "confidence": 0.85, "source": "ml"}
    ],
    "suggested_diagnostics": [...],
    "suggested_treatments": [...],
    "suggested_products": [...],
    "red_flags": [...],
    "follow_up_questions": [...],
    "disclaimer": "..."
  },
  "entities": {...}
}
```

#### Add Turn (`POST /consultations/{id}/turns`)
```json
{
  "intake": {
    "channel": "chat",
    "text": "Pesan tambahan..."
  }
}
```

---

## 🎨 Design System

Mengikuti desain yang sudah ada di `web/index.html`:

| Variable | Value |
|----------|-------|
| Background | `#0f1420` (dark blue gradient) |
| Panel | `#181f2e` / `#1f2838` |
| Border | `#2a3445` |
| Text | `#e7ecf3` |
| Muted | `#94a3b8` |
| Accent | `#38bdf8` (sky blue) → `#818cf8` (indigo) gradient |
| Success | `#34d399` |
| Warning | `#fbbf24` |
| Error | `#f87171` |
| Radius | `14px` (cards), `9px` (inputs) |

### Accessibility (a11y) Basics
- Semantic HTML structure
- High contrast text (WCAG AA compliant)
- Focus states on interactive elements
- Keyboard navigation support
- Responsive font sizes

---

## 📁 File yang Diubah/Dibuat

| File | Status | Keterangan |
|------|--------|------------|
| `web/telekonsultasi.html` | ✅ Baru | Halaman utama telekonsultasi (SPA) |
| `web/index.html` | ✅ Diubah | Tambah link ke `/telekonsultasi.html` |

---

## 🚀 Cara Menjalankan

1. **Start backend server:**
   ```bash
   cd "/Users/winnerharry/Naincode AI Dept/projects/sobatpaws-ai"
   export PYTHONPATH=src
   uvicorn sobatpaws.api.main:app --reload --port 8000
   ```

2. **Akses halaman:**
   - Dashboard: http://localhost:8000/
   - **Telekonsultasi**: http://localhost:8000/telekonsultasi.html
   - API Docs: http://localhost:8000/docs

---

## ⏭️ Next Steps (Untuk Pengembangan Selanjutnya)

1. **Authentication**
   - Saat ini menggunakan mock `vet_id=1`, `owner_id=1`, `pet_id=1`
   - Perlu integrasi dengan sistem auth (Auth0/Supabase/Custom)
   - Header `X-Sobatpaws-Key` untuk API key auth

2. **Real-time (Socket.io)**
   - ADR-002 merencanakan Socket.io untuk real-time update
   - Typing indicator
   - AI suggestion streaming
   - Doctor presence

3. **State Management**
   - Saat ini state disimpan di variabel JS sederhana
   - Untuk production: TanStack Query + React Context
   - Offline support: IndexedDB

4. **File Upload**
   - Placeholder untuk mic/camera
   - Integrasi dengan `POST /consultations/{id}/media`
   - Drag & drop gambar

5. **Doctor Input & Feedback**
   - UI untuk `POST /consultations/{id}/doctor-input`
   - UI untuk `POST /consultations/{id}/feedback`
   - Rating saran AI (correct/partial/incorrect)

6. **Next.js Migration**
   - ADR-002 merekomendasikan Next.js 16 App Router
   - Komponen React + TypeScript strict
   - shadcn/ui + Tailwind
   - TanStack Query untuk caching
   - OpenAPI TypeScript generation

---

## 🐾 Spesies yang Didukung

Dari `data/categories.json`:
- 🐕 Anjing (dog)
- 🐱 Kucing (cat)
- 🐰 Kelinci (rabbit)
- 🐹 Hamster (hamster)
- 🐔 Unggas (poultry)
- 🐟 Ikan (fish)
- 🦎 Reptil (reptile)
- 🐸 Amfibi (amphibian)
- 🦨 Musang Ferret (ferret)
- 🐹 Marmut (guinea_pig)

---

## 📝 Catatan

- **MVP Scope**: Halaman ini adalah MVP yang menunjukan alur dasar
- **Mock IDs**: Untuk demo, menggunakan `vet_id=1`, `owner_id=1`, `pet_id=1`
- **Same-Origin**: Menggunakan `API = ""` sehingga request ke origin yang sama
- **Backend Required**: Membutuhkan server FastAPI berjalan di port yang sama
