# Phase 19: PWA, Push Notifications, and Hydration Offline Sync

This phase introduces installable web-app behavior, browser push notifications, and resilient hydration logging when users are offline.

## What was added

- PWA install metadata (`manifest` + icon set).
- Service worker (`frontend/public/sw.js`) for shell/resource caching.
- Push-notification plumbing (VAPID-based configuration).
- Hydration offline queue with background synchronization.
- Migration requirement for hydration/push persistence (`migrations/008_pwa_push_hydration.sql`).

## Icon and visual system

The Metabolic OS icon direction uses:
- dark charcoal background (`#161921`)
- emerald progression arrow motif
- cyan pulse-line accent
- variants for 192, 512, maskable, and Apple touch usage

Assets are stored under `frontend/public/icons/` and related public assets.

## Installation flow

1. Deploy frontend with `manifest`, icons, and service worker files available.
2. Open the app in a mobile-capable browser.
3. Accept push permission when prompted by the UI.
4. Install the app:
   - **iOS Safari**: Share → Add to Home Screen
   - **Android Chrome**: Menu → Install app

## Backend prerequisites

Set the following env variables before enabling push in production:
- `VAPID_PUBLIC_KEY`
- `VAPID_PRIVATE_KEY`
- `VAPID_SUBJECT`

Also apply DB migration:

```bash
# migration execution method depends on your workflow
# ensure migrations/008_pwa_push_hydration.sql has been applied
```

## Offline hydration behavior

- Hydration events can be captured locally while offline.
- Events are queued in browser storage.
- Service worker/background sync (`hydration-sync`) flushes queued events when connectivity returns.
- Failed retries remain queued until successful submission or manual clearing.

## Operational verification checklist

- Confirm `manifest` is detected by browser devtools.
- Confirm service worker is active and controlling page scope.
- Verify install prompt appears on supported clients.
- Test offline hydration logging and online replay.
- Validate push subscription creation and test notification delivery.

## Troubleshooting quick reference

- **No install prompt**: verify HTTPS + manifest validity + service worker scope.
- **Push not working**: check VAPID keys and browser permission state.
- **Hydration queue stuck**: inspect service worker logs and API auth/token validity.
