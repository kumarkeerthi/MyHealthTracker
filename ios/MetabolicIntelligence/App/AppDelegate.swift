import UIKit

final class AppDelegate: NSObject, UIApplicationDelegate {
    static weak var authManager: AuthManager?
    static weak var pushManager: PushManager?
    static weak var healthKitManager: HealthKitManager?

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey : Any]? = nil
    ) -> Bool {
        application.setMinimumBackgroundFetchInterval(UIApplication.backgroundFetchIntervalMinimum)
        return true
    }

    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        guard let authManager = AppDelegate.authManager, let pushManager = AppDelegate.pushManager else { return }
        pushManager.didRegister(tokenData: deviceToken, authManager: authManager)
    }

    func application(_ application: UIApplication, performFetchWithCompletionHandler completionHandler: @escaping (UIBackgroundFetchResult) -> Void) {
        guard let healthKitManager = AppDelegate.healthKitManager else {
            completionHandler(.noData)
            return
        }

        Task {
            await healthKitManager.manualRefreshSync()
            completionHandler(.newData)
        }
    }
}
