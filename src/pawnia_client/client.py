import httpx
class PawniaClient:
    def __init__(self, base_url, api_key, timeout=30):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=timeout, headers={"X-EkosistemSatwa-Key": api_key})
    def chat(self, message, session_id=None, pet_id=None):
        payload = {"message": message}
        if session_id: payload["session_id"] = session_id
        if pet_id: payload["pet_id"] = pet_id
        resp = self.client.post(f"{self.base_url}/api/v1/ai/chat", json=payload)
        if resp.status_code == 401: raise Exception("Invalid API key")
        return resp.json()
    def triage(self, species, symptoms):
        return self.client.post(f"{self.base_url}/api/v1/ai/triage", json={"species":species,"symptoms":symptoms}).json()
    def recommend(self, species, diagnosis, symptoms=None):
        return self.client.post(f"{self.base_url}/api/v1/ai/treatment/recommend", json={"species":species,"diagnosis":diagnosis,"symptoms":symptoms or []}).json()
    def forecast(self, days=30, category="all"):
        return self.client.post(f"{self.base_url}/api/v1/ai/forecast/inventory", json={"days":days,"category":category}).json()
    def health_check(self):
        return self.client.get(f"{self.base_url}/health").json()
    def close(self): self.client.close()
    def __enter__(self): return self
    def __exit__(self, *args): self.close()
