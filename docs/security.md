# Security Hardening

## Controls implemented
- Rate-limiting middleware (IP + path sliding window)
- JSON input sanitization against script injection patterns
- Strict CORS allowlist via environment configuration
- JWT access tokens with expiration (`exp`)
- Admin-only dependency for restricted endpoints
- LLM usage cap per user per rolling hour
- Image upload byte-size limit enforcement

## Recommended operations
- Rotate JWT secrets regularly.
- Keep `CORS_ALLOWED_ORIGINS` limited to trusted domains.
- Use HTTPS termination at ingress (nginx / cloud LB).
- Route logs to SIEM for anomaly detection.
