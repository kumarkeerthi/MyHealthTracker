import UIKit

final class AppDelegate: NSObject, UIApplicationDelegate {
    static weak var authManager: AuthManager?
    static weak var pushManager: PushManager?

    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        guard let authManager = AppDelegate.authManager, let pushManager = AppDelegate.pushManager else { return }
        pushManager.didRegister(tokenData: deviceToken, authManager: authManager)
    }
}
