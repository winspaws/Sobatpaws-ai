# Security Analysis & Hardening: Sobatpaws AI + Pawnia AI

**Versi:** 1.0.0 | **Tanggal:** 28 Juni 2026 | **Oleh:** Wins (PM, Naincode AI Dept)

---

## Priority Matrix

| Priority | Issue | Status | Impact |
|----------|-------|--------|--------|
| P0 | CORS wildcard `*` -> specific origins | **FIXED** | Any website can call API |
| P0 | No HTTPS/SSL on VPS | **OPEN** | Data in transit unencrypted |
| P0 | No rate limiting | **OPEN** | DDoS, brute force |
| P1 | Firewall (iptables) ACCEPT all | **OPEN** | All ports exposed |
| P1 | No failed login attempt tracking | **OPEN** | Brute force JWT login |
| P1 | No file upload validation (size/type) | **OPEN** | Malware upload |
| P2 | JWT short expiry but no refresh rotation | Partial | Token reuse |
| P3 | Docker non-root user | **GOOD** | Container escape mitigation |
| P3 | SQLAlchemy ORM (no raw SQL) | **GOOD** | SQL injection protected |
| P3 | No sensitive data in logs | **GOOD** | Privacy protected |

---

## 1. CORS (FIXED)

**Before:** `allow_origins=["*"]` - any website could call API
**After:** Configurable via env `SOBATPAWS_CORS_ORIGINS`

Production: set `SOBATPAWS_CORS_ORIGINS=https://admin.sobatpaws.com,https://app.sobatpaws.com`
Dev default: `localhost:3000,localhost:3333,localhost:8080`

## 2. HTTPS/SSL (OPEN - HIGH PRIORITY)

**Problem:** API runs on HTTP (port 8080). JWT tokens, medical records, API keys sent in plain text. Vulnerable to MITM.

**Solution:** Let's Encrypt + Nginx reverse proxy
```bash
sudo apt install nginx certbot python3-certbot-nginx -y
# Configure reverse proxy pointing to 127.0.0.1:8080
sudo certbot --nginx -d api.sobatpaws.com
```

Add security headers:
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header X-XSS-Protection "1; mode=block" always;
```

## 3. Rate Limiting (OPEN)

**Problem:** No rate limiting - attacker can brute force login, DDoS API.

**Solution:** SlowAPI
```bash
pip install slowapi
```
Rate limits per endpoint:
- /auth/login: 5/minute (brute force protection)
- /api/v1/ai/chat: 30/minute (token cost)
- /api/v1/integration/*: 60/minute (admin panel)
- /health: 60/minute (monitoring)

## 4. Firewall (iptables) (OPEN)

**Problem:** All ports open, PostgreSQL port 5432 exposed.

**Solution:**
```bash
sudo iptables -P INPUT DROP
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT  # SSH
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT   # HTTP
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT  # HTTPS
sudo iptables -A INPUT -p tcp --dport 8080 -s 127.0.0.1 -j ACCEPT  # API only localhost
sudo iptables -A INPUT -p tcp --dport 5432 -s 172.18.0.0/16 -j ACCEPT  # DB only Docker
sudo apt install iptables-persistent -y
sudo netfilter-persistent save
```

## 5. JWT Security (Partial)

**Current:** JWT expiry 1 hour, no refresh rotation, no blacklist.
**Improvements:**
- Add refresh token rotation
- Token blacklist (Redis/DB) for revoked tokens
- Rotate refresh token on each use

## 6. LLM Security - Prompt Injection (Partial)

**Threats:** Prompt injection, jailbreaking, data leakage.
**Current:** Basic safety layer with poison rules, medical disclaimer.
**Improvements:**
```python
def sanitize_llm_input(text: str) -> str:
    # Remove injection patterns
    text = re.sub(r'ignore all (previous|above|prior) instructions', '', text, flags=re.IGNORECASE)
    return text[:2000]  # Max length

def validate_llm_output(text: str) -> bool:
    forbidden = ['definitive diagnosis', 'guaranteed cure', '100% effective']
    return not any(f in text.lower() for f in forbidden)
```

## 7. File Upload Security (OPEN)

**Problem:** Vision endpoint accepts files without size/type validation.
**Solution:**
```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"]
# Validate content type AND file signature (magic bytes)
```

## 8. Secrets Management (OPEN)

**Problem:** API keys and Telegram credentials in plain .env file.
**Solution:** Docker secrets or Vault for production.

## 9. Docker Security

**Already good:** Non-root user, internal network, restart policy.
**Improvements:**
```yaml
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
read_only: true
tmpfs:
  - /tmp
```

## 10. Security Checklist

### Immediate (24h)
- [ ] Setup HTTPS via Let's Encrypt + Nginx
- [ ] Configure iptables firewall
- [ ] Install rate limiting (SlowAPI)
- [ ] Add file upload validation

### Short-term (1 week)
- [ ] Add failed login tracking and account lockout
- [ ] Rotate all API keys and secrets
- [ ] Add JWT refresh token rotation
- [ ] Add Docker security options

### Medium-term (1 month)
- [ ] Setup audit logging system
- [ ] Implement secrets management (Vault/Docker secrets)
- [ ] Enable PostgreSQL encryption for PII
- [ ] Setup automated security scanning

## 11. Security Score: 3.3/10

| Category | Score | Status |
|----------|:-----:|--------|
| API Security (CORS, Auth) | 7/10 | CORS fixed, JWT partial |
| Network Security (HTTPS, Firewall) | 2/10 | HTTPS missing, iptables open |
| Rate Limiting | 0/10 | Not implemented |
| LLM Security | 5/10 | Basic safety layer exists |
| File Upload | 0/10 | No validation |
| Secrets Management | 3/10 | Plain text .env |
| Docker Security | 6/10 | Non-root user OK, no cap drop |
| Database Security | 5/10 | Internal network, no encryption |
| Audit Logging | 2/10 | Minimal logging |
| **Overall** | **3.3/10** | **Needs major improvements** |
