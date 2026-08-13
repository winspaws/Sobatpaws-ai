# Project Status — Ekosistem Satwa

## Current Status: 27 Jun 2026

### 🟢 Production
- **API**: ✅ Healthy (sobatpaws-api, workers=1)
- **DB**: ✅ Healthy (sobatpaws-db, PostgreSQL, 8 days uptime)
- **VPS**: ✅ 43.129.56.221, 35% disk, 56% RAM
- **LLM**: ✅ Available (SumoPod deepseek-v4-pro primary)

### 📊 Knowledge Base
- **316,100** diseases across 11 species
- **177** breeds, **437** symptoms
- **424MB** JSON files (cached via lru_cache, cold ~20s → warm <1s)

### 🤖 Pawnia AI Orchestrator
- 9 specialist agents aktif
- Multi-turn conversation support
- Risk classification (low/medium/severe/critical)
- Intent detection + agent routing

### 🔧 Recent Optimizations
- orjson for 10x faster JSON parsing
- lru_cache on load_knowledge_base (load once)
- Health endpoint lightweight + llm_available
- Admin dashboard multi-turn testing chat
- Disk cleanup: 79% → 35% (-25GB)

### 🔒 Remaining Blockers
- HTTPS/SSL — no domain DNS pointing to VPS
- Rate limiting — ✅ in-process middleware (`RATE_LIMIT_PER_MINUTE`, default 120/IP)

### 📦 Tech Stack
- **Runtime**: Python 3.11, FastAPI, Uvicorn
- **AI**: SumoPod (deepseek-v4-pro), Ollama (llama3.2 fallback)
- **ML**: scikit-learn, pandas, numpy
- **Vector Search**: ChromaDB
- **DB**: PostgreSQL (sobatpaws-db)
- **Deployment**: Docker, Docker Compose
