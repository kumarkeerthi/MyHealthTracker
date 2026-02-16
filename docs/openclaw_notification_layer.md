# OpenClaw Messaging + Notification Layer

## Webhook implementation

### `POST /whatsapp-message`
- Accepts inbound WhatsApp text (`text`) and `user_id`.
- Runs LLM parsing + rule validation through existing `llm_service.analyze`.
- Returns a structured coaching response with:
  - `approval_status`
  - `insulin_load_delta`
  - `suggested_action`
- Emits outbound WhatsApp-formatted coaching message via `notification_service.send_message`.

### `POST /notification-event`
- Accepts provider/system events with `event_type` + custom `payload`.
- Standardized as a push-channel dispatch pipeline.
- Returns normalized delivery result (`sent` or `skipped`).

## OpenClaw integration plan

1. **Inbound wiring**
   - Configure OpenClaw webhook target:
     - `POST {backend_url}/whatsapp-message`
     - `POST {backend_url}/notification-event`
2. **Authentication**
   - Add `X-OpenClaw-Signature` HMAC verification (recommended next step).
3. **Idempotency**
   - Include OpenClaw event/message id in payload and dedupe before processing.
4. **Delivery receipts**
   - Relay OpenClaw status callbacks to `/notification-event` for analytics.
5. **Retries**
   - Keep webhook handlers fast (< 2s) and push long work to background queue if volume grows.

## Message formatting template

Use this response shape for coaching messages:

```json
{
  "channel": "whatsapp",
  "title": "Metabolic coaching response",
  "body": "Status: APPROVED|REJECTED\\nReason: <rules + rationale>\\nAction: <next best action>",
  "insulin_load_delta": 12.4,
  "approval_status": "approved",
  "suggested_action": "Pair dosa with paneer + salad and halve portion."
}
```

Suggested WhatsApp text style:

- Line 1: status emoji + verdict
- Line 2: short reason
- Line 3: one action only
- Line 4: optional macro headroom

## Cron scheduler setup

Daily coaching automation is configured with APScheduler cron jobs:

- 08:00 UTC → "Protein first."
- 13:00 UTC → "Eat vegetables before chapati."
- 18:00 UTC → "If hungry, drink water. Fasting window active."

Scheduler lifecycle:
- starts on FastAPI startup (`coaching_scheduler.start()`)
- stops on shutdown (`coaching_scheduler.shutdown()`)

## Alert rules

Triggered while logging food:

- If insulin score > 70:
  - Push: "High carb load detected. 20 min walk suggested."
- If daily protein < 80g:
  - Push: "HDL support compromised."
