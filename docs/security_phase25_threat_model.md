# Phase 25 Threat Model Summary

## Scope
- FastAPI backend API routes, especially `/auth/*`, `/analyze-food-image`, and `/llm/analyze`.
- iOS login/auth session flow.
- Production deployment defaults in `docker-compose.prod.yml`.

## Primary threats and mitigations

1. **Credential stuffing and brute-force login abuse**
   - Added route-level and login-level rate limits.
   - Persisted failed login attempts and account lockouts.
   - Added audit events for failed/successful login attempts.

2. **LLM abuse (spam, prompt injection, malformed outputs)**
   - Separate `/llm` rate limits plus hourly and daily user caps.
   - Input-length limits and prompt-injection pattern checks.
   - Locked system prompt + strict JSON schema response mode.
   - Server-side strict output validation and malformed output rejection.
   - Token cap (`LLM_MAX_TOKENS`) on LLM requests.

3. **Upload abuse and malicious file uploads**
   - Increased file-size policy to explicit 5 MB max.
   - Enforced MIME allow-list (`image/jpeg`, `image/png`, `image/webp`).
   - Suspicious uploads are audit logged.

4. **Web attack surface (transport/header/cross-site risks)**
   - HTTPS enforcement middleware.
   - HSTS + secure response headers middleware.
   - CSRF checks for unsafe HTTP methods (origin/referer validation).
   - CORS remains restricted via configured allowed origins.

5. **Observability and incident response gaps**
   - Added `security_audit_logs` table for suspicious events.
   - Added `llm_usage_daily` table to enforce daily LLM usage limits.
   - Events recorded for failed logins, suspicious prompts/uploads, and excess LLM calls.

## Residual risk and next steps
- Introduce distributed rate limiting (Redis) for multi-instance consistency.
- Add SIEM/export pipeline for `security_audit_logs`.
- Add anomaly alerts (e.g., bursts of failed logins per ASN / geo).
- Consider WAF managed rules for bot and scraping mitigation.
