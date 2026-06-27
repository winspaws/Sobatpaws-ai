# Ekosistem Satwa — Status Dashboard

> Last updated: 2026-06-27 10:45 WIB

## Sprint Progress

| Sprint | Status | Tasks |
|--------|:------:|:-----:|
| Sprint 1-5 | ✅ 100% | Foundation, Rebranding, Pawnia, Admin, KB |
| Sprint 6 | ✅ 100% | Monitoring, API v2, Forecasting, Telegram, Rate Limiting |

## Knowledge Base

| Metrik | Value |
|--------|:-----:|
| **Total Active Diseases** | 11,000 (1,000/species) |
| **Total Generated** | 315,496 |
| **Target** | 350,000 diseases |
| **Expansion** | Auto setiap 10 menit via cron |
| **Species** | 11 |

## AI Providers

| Provider | Type | Status |
|----------|:----:|:------:|
| OpenAI | openai | ✅ Active |
| Anthropic Claude | anthropic | ✅ Active |
| SumoPod AI | custom | ✅ Active (deepseek-v4-flash) |
| Qwen (Alibaba) | custom | ✅ Active (qwen-max) |
| Local LLM | local_llm | ✅ Active (llama3.2) |

## Admin Dashboard

- URL: `http://43.129.56.221:8080/admin`
- Pages: Dashboard, KB, Testing, Settings, AI Providers, Token Usage

## Services

| Service | Status | Port |
|---------|:------:|:----:|
| API | ✅ Healthy | :8080 |
| Database | ✅ Healthy | :5432 |
| Monitoring | ✅ Active | Grafana + Prometheus |
| KB Expansion | ✅ Every 10min | Cron |
