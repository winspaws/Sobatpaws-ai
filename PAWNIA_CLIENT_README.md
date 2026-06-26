# Pawnia Client SDK

Python client for Pawnia AI Orchestrator.

## Install

```bash
pip install pawnia-client
```

## Quick Start

```python
from pawnia_client import PawniaClient
client = PawniaClient(base_url="http://43.129.56.221:8080", api_key="your-key")
response = client.chat(message="Kucing saya muntah")
print(response.suggestion.text)
```

## Endpoints

- chat -> POST /api/v1/ai/chat
- triage -> POST /api/v1/ai/triage
- recommend -> POST /api/v1/ai/treatment/recommend
- forecast -> POST /api/v1/ai/forecast/inventory
- screening -> POST /api/v1/integration/appointment/screening
- medical_history -> GET /api/v1/integration/customer/{id}/medical-history
