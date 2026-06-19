# ADR-002: Frontend Telekonsultasi Architecture

## Status
Proposed

## Context
Sobatpaws membutuhkan antarmuka frontend untuk:
1.  Dokter hewan menerima dan menjawab konsultasi
2.  Pemilik hewan mengirim intake gejala, foto, suara
3.  Real time sync antara AI suggestion dan input dokter
4.  Audit trail seluruh interaksi konsultasi

Alternatif stack:
- ✅ Next.js 16 App Router
- ✅ TypeScript Strict Mode
- ✅ TanStack Query untuk state management
- ✅ Socket.io untuk real time update
- ❌ Single Page App vanilla (tidak scalable)
- ❌ Remix (tim tidak familiar)
- ❌ React Server Components only (butuh interaktivitas tinggi)

## Decision
Arsitektur frontend telekonsultasi:

```
┌──────────────────────────────────────────────────┐
│  Next.js 16 App Router                           │
│  ├─ /telekonsultasi/[id]  (halaman konsultasi)   │
│  ├─ /dashboard          (dokter dashboard)       │
│  └─ /intake             (form intake pemilik)    │
└───────────────────┬──────────────────────────────┘
                    │
        ┌───────────▼────────────┐
        │ TanStack Query v5      │
        │  - Caching             │
        │  - Background refresh  │
        │  - Optimistic update   │
        └───────────┬────────────┘
                    │
        ┌───────────▼────────────┐
        │ Socket.io Client       │
        │  - Real time AI update │
        │  - Doctor presence     │
        │  - Typing indicator    │
        └───────────┬────────────┘
                    │
        ┌───────────▼────────────┐
        │ Sobatpaws FastAPI      │
        │  /api/consultations/*  │
        │  /api/ai/suggest       │
        └────────────────────────┘
```

### Prinsip desain:
1.  **Offline first**: Semua input disimpan di IndexedDB sebelum dikirim ke server
2.  **Idempotent**: Semua aksi konsultasi memiliki request id unik
3.  **Audit log**: Semua perubahan state konsultasi dicatat secara urut
4.  **Progressive enhancement**: Konsultasi dapat berjalan meskipun AI offline
5.  **Accessibility**: WCAG 2.1 AA compliant untuk dokter yang menggunakan screen reader

## Consequences

### Positif
-   Real time experience untuk dokter dan pemilik
-   Optimis UI tidak nge-lag ketika jaringan lambat
-   Type safety end-to-end dari OpenAPI schema
-   Built-in support untuk image upload dan stream audio
-   Mudah diintegrasikan dengan app mobile nanti

### Negatif
-   Kompleksitas state management bertambah
-   Perlu handle race condition antara AI suggestion dan input dokter
-   Socket connection management di mobile background
-   Ukuran bundle lebih besar dari vanilla

### Risiko
-   Memory leak pada long lived consultation session
-   Sync conflict ketika dokter edit ketika AI sedang generate
-   Performance ketika konsultasi berjalan > 1 jam

## Next Steps
1.  Generate TypeScript client dari OpenAPI schema
2.  Implementasikan consultation state machine
3.  Setup Socket.io server di backend
4.  Buat intake form multi step
5.  Buat komponen AI suggestion dengan diff doctor input
