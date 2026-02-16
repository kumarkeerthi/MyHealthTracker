# Phase 19: PWA + Push + Hydration

## Icon design description
Metabolic OS icon uses a minimalist shield outline on dark charcoal (`#161921`) with:
- Emerald upward arrow at center (discipline/progression signal)
- Subtle cyan metabolic pulse line crossing lower center
- Clean geometric spacing tuned for elite, calm visual tone
- Generated variants provided as SVG assets for 192/512/maskable concepts, plus apple-touch icon SVG

## PWA install instructions
1. Deploy frontend with `manifest.json`, icons, and `sw.js` in `frontend/public`.
2. Open app in mobile browser and tap **Enable Push Notifications** to allow alerts.
3. Use the install prompt banner: **Install Metabolic OS for full experience.**
4. If prompt is not shown:
   - iOS Safari: Share → Add to Home Screen
   - Android Chrome: Menu → Install app
5. Set `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, and `VAPID_SUBJECT` in backend `.env`.
6. Apply `migrations/008_pwa_push_hydration.sql` before enabling hydration/push endpoints.

## Offline behavior
- Service worker caches dashboard shell and network responses.
- Hydration quick logs queue offline in localStorage.
- Background sync (`hydration-sync`) flushes queued hydration events when connectivity resumes.
