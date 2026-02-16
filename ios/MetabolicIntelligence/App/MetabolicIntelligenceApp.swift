import SwiftUI

@main
struct MetabolicIntelligenceApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @StateObject private var authManager = AuthManager()
    @StateObject private var syncManager = SyncManager()
    @StateObject private var pushManager = PushManager()
    @StateObject private var healthKitManager = HealthKitManager()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(authManager)
                .environmentObject(syncManager)
                .environmentObject(pushManager)
                .environmentObject(healthKitManager)
                .preferredColorScheme(.dark)
                .task {
                    AppDelegate.authManager = authManager
                    AppDelegate.pushManager = pushManager
                    await authManager.restoreSession()
                    await pushManager.configureIfNeeded(authManager: authManager)
                    await healthKitManager.bootstrap(authManager: authManager, syncManager: syncManager)
                    await syncManager.flushPendingIfNeeded(authManager: authManager)
                }
        }
    }
}
