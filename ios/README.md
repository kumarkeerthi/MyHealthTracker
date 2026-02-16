# Metabolic Intelligence iOS (SwiftUI + HealthKit)

This folder contains a native iOS 16+ SwiftUI MVVM scaffold for the Metabolic Intelligence mobile app.

## Project structure

- `MetabolicIntelligence/App`
  - `MetabolicIntelligenceApp.swift` app entry, dependency bootstrapping
  - `RootView.swift` auth gate
- `MetabolicIntelligence/Views`
  - `LoginView`, `DashboardView`, `BodyView`, `StrengthView`, `AnalyticsView`, `ProfileView`, `ScanFoodView`, `SettingsView`
  - `CameraPicker.swift` camera integration wrapper
  - `Theme.swift` dark/emerald visual identity
- `MetabolicIntelligence/ViewModels`
  - `DashboardViewModel.swift`
- `MetabolicIntelligence/Managers`
  - `AuthManager.swift` JWT login/logout/session restore using Keychain
  - `HealthKitManager.swift` permissions + daily sync + post-meal walk forwarding
  - `PushManager.swift` APNs permission + backend subscription
  - `KeychainHelper.swift` secure storage utility
  - `SyncManager.swift` offline replay manager
- `MetabolicIntelligence/Services`
  - `APIClient.swift` URLSession networking + typed request helpers
- `MetabolicIntelligence/Persistence`
  - `OfflineStore.swift` local cache queue for offline mode
- `MetabolicIntelligence/Models`
  - API request/response models
- `MetabolicIntelligence/Resources/Assets.xcassets`
  - `AppIcon.appiconset` icon assets

## Implemented backend endpoints

- `POST /login`
- `GET /daily-summary`
- `POST /log-food`
- `POST /log-vitals`
- `POST /log-exercise`
- `POST /analyze-food-image`
- `POST /push/subscribe`

## Sample API calls

```swift
// Login
try await authManager.login(email: "you@example.com", password: "••••••••")

// Daily summary
await dashboardViewModel.load(token: token)

// Log food
try await APIClient.shared.requestNoResponse(path: "log-food", token: token, payload: foodPayload)

// Analyze camera image
let analysis = try await APIClient.shared.uploadImage(path: "analyze-food-image", token: token, imageData: imageData)
```

## Setup notes for Xcode

1. Create an iOS App target (`iOS 16.0+`) and add files from `MetabolicIntelligence/`.
2. Enable **HealthKit** capability.
3. Enable **Push Notifications** and Background Modes (remote notifications).
4. Add camera permission key in `Info.plist`:
   - `NSCameraUsageDescription`
5. Add HealthKit usage descriptions:
   - `NSHealthShareUsageDescription`
   - `NSHealthUpdateUsageDescription` (if write access added later)


## App icon generation (text-only repository friendly)

PNG AppIcon binaries are intentionally **not committed** to keep PR diffs text-only.
Generate them locally before building in Xcode:

```bash
python ios/scripts/generate_app_icons.py
```

This writes all required `icon-*.png` files into the AppIcon asset catalog based on the committed SVG design.
