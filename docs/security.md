# Security Hardening Guide

This document summarizes security controls currently implemented and the operational practices required to keep them effective.

## Implemented controls

### 1) Request-path protection
- **Rate limiting middleware**: per-IP and path-aware request throttling with configurable limits.
- **Input sanitization middleware**: rejects payload patterns commonly associated with script injection.
- **CSRF middleware**: additional request-origin safety for state-changing flows.
- **Auth-required middleware**: central enforcement to block unauthenticated access to protected routes.

### 2) Transport and browser security
- **HTTPS redirect enforcement**: traffic is upgraded toward secure transport expectations.
- **Security headers middleware**: response headers harden browser behavior and reduce attack surface.
- **Strict CORS allowlist**: controlled by environment (`CORS_ALLOWED_ORIGINS`) to prevent permissive cross-origin access.

### 3) Identity and privilege controls
- **JWT tokens with expiration (`exp`)** reduce replay window for stolen tokens.
- **Admin-only dependency checks** protect restricted endpoints.
- **Token/user consistency checks** on sensitive sync-style endpoints.

### 4) Abuse and cost containment
- **LLM usage caps** enforce per-user request ceilings in rolling windows.
- **Image upload size limits** mitigate memory pressure and payload abuse.
- **Route-specific burst controls** (e.g., stricter `/llm` policy) limit high-cost endpoint misuse.

## Configuration checklist

Review these env variables during every deployment:

- `JWT_SECRET_KEY`
- `JWT_EXPIRE_MINUTES`
- `CORS_ALLOWED_ORIGINS`
- `RATE_LIMIT_REQUESTS`
- `RATE_LIMIT_WINDOW_SECONDS`
- `LLM_REQUESTS_PER_HOUR`
- `MAX_FOOD_IMAGE_BYTES`

## Operational best practices

- Rotate JWT secrets on a defined cadence and after any incident.
- Keep CORS origins minimal (only trusted web domains).
- Terminate TLS at ingress (nginx or managed load balancer).
- Forward structured logs into centralized SIEM/observability tooling.
- Monitor spikes on `/auth/*`, `/llm/*`, and upload endpoints.
- Patch base images and Python dependencies on a regular schedule.

## Recommended validation routine (post-deploy)

1. Confirm unauthenticated requests to protected routes return 401/403.
2. Send burst traffic to verify rate-limit responses trigger as expected.
3. Validate CORS behavior from allowed and disallowed origins.
4. Confirm JWT expiration and admin checks behave correctly.
5. Verify health and metrics endpoints continue to operate under security middleware.

## Incident response quick-start

If suspicious activity is detected:
1. Rotate JWT secret and revoke active sessions where possible.
2. Tighten temporary rate limits.
3. Restrict CORS to absolute minimum.
4. Review recent logs for source IPs, tokens, and endpoint patterns.
5. Restore normal limits gradually after threat containment.
