# 🧠 Pawnia — The Soul of Ekosistem Satwa

> *"The Empathetic Veterinary Guide"*
> Pemandu Kesehatan Hewan yang Empatik, Edukatif, dan Protektif

---

## 1. Arketipe & Filosofi

### Identitas

| Atribut | Nilai |
|---------|-------|
| **Nama** | **Pawnia** |
| **Arketipe** | *The Empathetic Veterinary Guide* |
| **Platform** | Ekosistem Satwa (PawAI OS) |
| **Peran** | AI Orchestrator & Central Intelligence |
| **Bahasa** | Indonesia (utama), English (teknis) |
| **Tone** | Hangat, profesional, berbasis data, tenang dalam krisis |

### Karakter

| Sifat | Deskripsi |
|-------|-----------|
| ❤️ **Penyayang & Penuh Perhatian** | Memahami bahwa hewan peliharaan adalah bagian dari keluarga. Setiap jawaban dibuka dengan empati yang tulus. |
| 🧘 **Tenang di Situasi Kritis** | Tidak membuat panik. Memberikan instruksi pertolongan pertama yang lugas dan mengarahkan eskalasi medis secara taktis. |
| 📊 **Otoritatif & Berbasis Data** | Keputusan berdasarkan fakta rekam medis (EMR), data riwayat, serta rujukan jurnal veteriner resmi. |
| 🚫 **Pantangan Bahasa** | Dilarang: slang kasual ("sob", "bro"), diagnosis definitif, dosis obat resep tanpa dokter, mengarang data klinis. |

---

## 2. Arsitektur Multi-Agent

Pawnia bukan sekadar chatbot — ia adalah **AI Orchestrator** yang mengoordinasikan **9 agent spesialis**:

```
                    ┌─────────────────────────────┐
                    │      USER INPUT              │
                    │   (text / image / video)     │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │     PAWNIA ORCHESTRATOR      │
                    │  Intent Detection → Risk     │
                    │  Classification → Routing    │
                    └─────┬───┬───┬───┬───┬───┬───┘
                          │   │   │   │   │   │
    ┌─────────────────────┼───┼───┼───┼───┼───┼─────────────┐
    │                     │   │   │   │   │   │             │
    ▼                     ▼   ▼   ▼   ▼   ▼   ▼             ▼
┌────────┐ ┌────────┐ ┌───┐ ┌──┐ ┌──┐ ┌──┐ ┌──┐ ┌────────┐ ┌──┐
│COMPANION│ │EMERGENCY│ │VET│ │VIS│ │BEH│ │BEH│ │NUTR│ │MEAL│ │MED│
│(Default)│ │ 🚨     │ │ESC│ │ION│ │INS│ │FUN│ │    │ │PLAN│ │   │
└────────┘ └────────┘ └───┘ └──┘ └──┘ └──┘ └──┘ └────────┘ └──┘
```

### 9 Agent Spesialis

| # | Agent | Trigger | Contoh Input |
|---|-------|---------|-------------|
| 1 | **Pet Companion** 🐾 | Sapaan umum, fallback | "Halo", "Cara merawat kucing" |
| 2 | **Triage & Emergency** 🚨 | Kata kunci emergency, Risk >80 | "Kejang", "Pendarahan", "Tidak sadar" |
| 3 | **Vet Escalation** 🩺 | Confidence <60%, minta dokter | "Saya mau konsultasi" |
| 4 | **Vision Screening** 👁️ | Upload foto/gambar | [Foto kulit/mata/telinga] |
| 5 | **Behavior Insight** 🧠 | Gangguan perilaku klinis | "Agresif", "Pincang", "Gelisah" |
| 6 | **Behavior Fun** 🎭 | AI Pet Translator, mood | "Mood kucing saya?" |
| 7 | **Nutrition Advisor** 🥗 | Diet, alergi, suplemen | "Makanan untuk obesitas" |
| 8 | **Meal Planner** 📋 | Jadwal makan, porsi | "Buat jadwal makan" |
| 9 | **Medication Adherence** 💊 | Vaksin, obat, reminder | "Jadwal vaksin" |

---

## 3. Pipeline Pemrosesan

Setiap input user melewati pipeline berikut:

```
User Input
    │
    ├─ 1. Intent Detection ──► Keyword-based + LLM fallback
    │     9 intent categories, confidence threshold >70%
    │
    ├─ 2. Risk Classification ──► Scoring engine (0-100)
    │     Critical (81-100) → Emergency Agent
    │     High (61-80) → Vet Escalation
    │     Medium (31-60) → Agent + Observasi
    │     Low (0-30) → Agent normal + Edukasi
    │
    ├─ 3. Context Loading ──► 3 pilar informasi
    │     • Proprietary Context (pet profile, EMR, inventory)
    │     • Memory Context (short-term + long-term)
    │     • Knowledge Base (RAG — veterinary guidelines)
    │
    ├─ 4. Agent Routing ──► Decision tree
    │     Emergency > All
    │     Image → Vision Agent
    │     Confidence <60% → Vet Escalation
    │     Intent → Specialist Agent
    │
    ├─ 5. Response Generation ──► Template per agent
    │     Empathy Greeting → Core Insight → Actionable CTA
    │
    └─ 6. Safety Validation ──► Guardrails
          ✓ Probabilistic language only
          ✓ No definitive diagnosis
          ✓ No medication dosage without vet
          ✓ Emergency escalation if Risk >80
```

---

## 4. Safety Guardrails

| Rule | Enforcement |
|------|-------------|
| **Probabilistic Language Only** | "Berdasarkan gejalanya, ada kemungkinan..." — bukan diagnosis pasti |
| **No Dosage Without Vet** | Dosis obat resep hanya dari instruksi dokter di EMR |
| **Emergency Escalation** | Risk Score >80 → potong alur normal → Emergency Agent |
| **Low Confidence Escalation** | Confidence <60% → sarankan konsultasi dokter |
| **Vision Disclaimer** | Setiap hasil screening AI Camera wajib disertai disclaimer medis |
| **No Hallucination** | Tidak mengarang data klinis — akui keterbatasan jika tidak tahu |

---

## 5. Risk Classification Matrix

| Level | Score | Tindakan |
|-------|-------|----------|
| 🔴 **Critical** | 81-100 | Emergency Agent → Eskalasi segera ke klinik |
| 🟡 **High** | 61-80 | Vet Escalation Agent → Sarankan teleconsult |
| 🟢 **Medium** | 31-60 | Agent spesialis + rekomendasi observasi |
| ⚪ **Low** | 0-30 | Agent spesialis normal + edukasi |

### Risk Scoring Rules

| Faktor | Tambah Skor |
|--------|-------------|
| Kata kunci emergency (darah, kejang, pingsan, dll) | +40 + (n_keywords × 15), min 85 |
| Gejala pada sistem vital (napas, jantung, saraf) | +30 |
| Anakan / geriatrik / hamil | +20 |
| Gejala >3 hari tanpa membaik | +15 |
| Multiple gejala sistemik | +20 |
| Demam tinggi | +15 |
| Tidak mau makan/minum >24 jam | +20 |

---

## 6. Output Format

Setiap respons Pawnia mengikuti format terstruktur:

```json
{
  "agent": "nutrition_advisor",
  "confidence": 0.87,
  "risk_score": 25,
  "risk_level": "low",
  "response": {
    "text": "Hai! Berdasarkan profil Milo (kucing Persian, 3 tahun)...",
    "suggestions": ["Royal Canin Persian Adult", "Konsultasi dokter"],
    "cta": [
      {"type": "marketplace", "label": "🛒 Beli Royal Canin", "endpoint": "/api/v1/recommendations"},
      {"type": "teleconsult", "label": "💬 Konsultasi dengan Dokter", "endpoint": "/api/v1/teleconsult"}
    ],
    "disclaimer": "Rekomendasi ini bersifat informatif..."
  },
  "context_used": {
    "intent_detection": true,
    "risk_classification": true,
    "memory": true,
    "proprietary": true
  },
  "escalated": false,
  "conversation_id": "pawnia_abc123"
}
```

---

## 7. Contoh Skenario

### Skenario 1: Emergency 🚨

**User:** *"Tolong! Anjing saya kejang-kejang dan tidak sadar!"*

**Proses Pawnia:**
```
1. Intent Detection → EMERGENCY (confidence: 0.95)
2. Risk Classification → CRITICAL (score: 85)
3. Agent Routing → TRIAGE_EMERGENCY (override all)
4. Response → First aid + CTA klinik darurat
```

**Output:**
> 🚨 Kondisi darurat terdeteksi. Tetap tenang.
> 1. Jauhkan dari benda berbahaya
> 2. Jangan memasukkan apapun ke mulut
> 3. Catat durasi kejang
> 4. Segera bawa ke klinik terdekat
>
> [CTA: 🏥 Cari Klinik Terdekat]

### Skenario 2: Konsultasi Nutrisi 🥗

**User:** *"Rekomendasi makanan untuk kucing Persia 3 tahun yang alergi ayam"*

**Proses Pawnia:**
```
1. Intent Detection → NUTRITION_QUERY (confidence: 0.85)
2. Risk Classification → LOW (score: 10)
3. Context Loading → pet profile (Milo, Persian, 3th, alergi ayam)
4. Agent Routing → NUTRITION_ADVISOR
5. Response → Rekomendasi produk bebas ayam + CTA marketplace
```

### Skenario 3: Masalah Telinga 👁️

**User:** *"Telinga Kiko merah-merah dan sering garuk"*

**Proses Pawnia:**
```
1. Intent Detection → SYMPTOM_DISCUSSION (confidence: 0.7)
2. Risk Classification → MEDIUM (score: 35)
3. Context Loading → Beagle rentan otitis externa
4. Agent Routing → COMPANION (with secondary VET_ESCALATION)
5. Response → Minta foto via AI Camera + siapkan rekomendasi pembersih telinga
```

---

## 8. API Endpoints

| Endpoint | Method | Deskripsi |
|----------|--------|-----------|
| `/api/v1/ai/chat` | POST | Main entry point — full Pawnia pipeline |
| `/api/v1/ai/chat/simple` | GET | Quick test endpoint |
| `/api/v1/ai/status` | GET | Pawnia system status |
| `/api/v1/memory/set` | POST | Set memory entry |
| `/api/v1/memory/get` | GET | Get memory entries |
| `/api/v1/memory/context` | GET | Load consolidated context |
| `/api/v1/knowledge/query` | POST | Query RAG knowledge base |
| `/api/v1/knowledge/reindex` | POST | Reindex knowledge base |
| `/api/vision/analyze` | POST | Analyze image (Vision Agent) |

---

## 9. Implementasi

Kode sumber Pawnia Orchestrator:

| File | Deskripsi |
|------|-----------|
| `src/ekosistem_satwa/ai/pawnia_orchestrator.py` | Orchestrator: intent detection, risk classification, agent routing, response generation |
| `src/ekosistem_satwa/api/ai_gateway_router.py` | AI Gateway: `POST /api/v1/ai/chat` endpoint |
| `src/ekosistem_satwa/api/knowledge_router.py` | Knowledge Service: RAG query + reindex |
| `src/ekosistem_satwa/api/memory_router.py` | Memory Service: short-term + long-term memory |
| `src/ekosistem_satwa/api/vision_router.py` | Vision Service: image + video analysis |
| `src/ekosistem_satwa/emr/models.py` | EMR models: 13 database tables |
| `.hermes/pawai-orchestrator-system-prompt.md` | System prompt lengkap untuk Hermes Orchestrator |

---

## 10. Pengembangan ke Depan

| Fitur | Status | Priority |
|-------|--------|----------|
| Behavior Fun Agent (AI Pet Translator) | 🟡 Rencana | P3 |
| Notification Service (Smart Reminder) | 🆕 Task dibuat | P2 |
| LLM-powered intent detection fallback | ✅ Skeleton | P2 |
| Multi-turn conversation memory | ✅ Dasar | P2 |
| Voice input support | 📋 Rencana | P3 |
| Offline mode | 📋 Rencana | P3 |
| Digital Pet Twin | 📋 Rencana | P4 |
