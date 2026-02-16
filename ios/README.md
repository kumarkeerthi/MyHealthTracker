# Metabolic Intelligence iOS (SwiftUI + HealthKit)

Private native iOS 16+ app scaffold focused on **performance**, **body progress**, and **strength identity**, while mirroring the web information architecture.

## SwiftUI MVVM project structure

- `MetabolicIntelligence/App`
  - `MetabolicIntelligenceApp.swift` app entry + dependency bootstrap
  - `RootView.swift` authentication gate
  - `AppDelegate.swift` APNs delegate hooks
- `MetabolicIntelligence/Views`
  - `DashboardTabView` 5-tab shell: Home / Body / Strength / Analytics / Profile
  - `DashboardView` (Home) insulin load ring + macro/hydration/movement cards
  - `BodyView` animated silhouette + weekly comparison + energy aura
  - `StrengthView` strength index meter + grip/pull-up/dead-hang/pushup trackers
  - `AnalyticsView`, `ProfileView`, `LoginView`, `ScanFoodView`, `SettingsView`
- `MetabolicIntelligence/ViewModels`
  - `DashboardViewModel.swift` Combine-powered state and Home sync
- `MetabolicIntelligence/Managers`
  - `AuthManager.swift` (JWT in Keychain)
  - `AuthenticationManager.swift` alias for naming parity
  - `HealthKitManager.swift` HealthKit permissions/queries/post-meal walk detection/sync
  - `SyncManager.swift` offline queue replay
  - `PushManager.swift` APNs setup + backend subscribe
  - `KeychainHelper.swift` secure storage
- `MetabolicIntelligence/Services`
  - `APIClient.swift` URLSession transport layer
  - `APIService.swift` app endpoint abstraction
- `MetabolicIntelligence/Persistence`
  - `OfflineStore.swift` cache for pending logs + last summary + last vitals
- `MetabolicIntelligence/Models`
  - typed API payloads + health/strength snapshots
- `MetabolicIntelligence/Resources/Assets.xcassets/AppIcon.appiconset`
  - Dark charcoal + emerald shield + upward pulse icon set

## HealthKit integration

`HealthKitManager` includes:

- `requestPermissions()`
- `fetchDailySteps()`
- `fetchRestingHR()`
- `fetchSleepHours()`
- `fetchWorkouts(since:)`
- `detectPostMealWalk()`
- `syncDailyVitals()` with batched backend sync

Read permissions requested:

- Step count
- Resting heart rate
- HRV (SDNN)
- Sleep analysis
- Workouts
- VO2 Max (if available)

### Post-meal walk logic

A walk bonus is set true if, within 60 minutes after last meal:

1. A walking workout exists, **or**
2. A step spike is detected relative to pre-meal baseline.

## Backend sync endpoints

- `POST /log-vitals`
- `POST /log-exercise`
- `POST /apple-sync`

`HealthKitManager.syncDailyVitals()` sends batched payload data and enqueues offline fallback events via `SyncManager`.

## Offline support

`OfflineStore` caches:

- last daily summary (`last-daily-summary.json`)
- last vitals (`last-vitals.json`)
- pending logs (`pending-events.json`)

`SyncManager.flushPendingIfNeeded()` retries in-order when network returns.

## Security

- JWT token persisted in Keychain (`AuthManager` + `KeychainHelper`)
- HTTPS-only API base URL in `APIClient`
- URLSession with connectivity-aware config

## HealthKit/permission Info.plist entries

Add to target `Info.plist`:

- `NSHealthShareUsageDescription` = "Metabolic Intelligence reads health metrics to power your daily body and strength dashboard."
- `NSHealthUpdateUsageDescription` = "Metabolic Intelligence may write selected workout metadata to improve coaching continuity."
- `NSCameraUsageDescription` = "Metabolic Intelligence uses the camera to scan meals for nutrition analysis."

## App icon generation

PNG icon files are generated from the committed vector design:

```bash
python ios/scripts/generate_app_icons.py
```

This writes required AppIcon sizes to:
`ios/MetabolicIntelligence/Resources/Assets.xcassets/AppIcon.appiconset/`
