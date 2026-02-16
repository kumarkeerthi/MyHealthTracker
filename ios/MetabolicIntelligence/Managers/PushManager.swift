import Foundation
import UserNotifications
import UIKit

@MainActor
final class PushManager: NSObject, ObservableObject {
    @Published var deviceToken: String?

    func configureIfNeeded(authManager: AuthManager) async {
        let center = UNUserNotificationCenter.current()
        do {
            let granted = try await center.requestAuthorization(options: [.alert, .badge, .sound])
            guard granted else { return }
            UIApplication.shared.registerForRemoteNotifications()
            if let token = deviceToken, let jwt = authManager.token {
                try? await APIClient.shared.requestNoResponse(
                    path: "push/subscribe",
                    token: jwt,
                    payload: PushSubscribePayload(deviceToken: token, platform: "ios")
                )
            }
        } catch {
            return
        }
    }

    func didRegister(tokenData: Data, authManager: AuthManager) {
        let token = tokenData.map { String(format: "%02.2hhx", $0) }.joined()
        deviceToken = token

        Task {
            guard let jwt = authManager.token else { return }
            try? await APIClient.shared.requestNoResponse(
                path: "push/subscribe",
                token: jwt,
                payload: PushSubscribePayload(deviceToken: token, platform: "ios")
            )
        }
    }
}
