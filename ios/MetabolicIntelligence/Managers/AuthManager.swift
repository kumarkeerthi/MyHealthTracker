import Foundation

@MainActor
final class AuthManager: ObservableObject {
    @Published private(set) var token: String?
    @Published private(set) var userId: String?
    @Published private(set) var refreshToken: String?

    var isAuthenticated: Bool { token != nil }

    private let service = "com.metabolicintelligence.auth"

    func login(email: String, password: String) async throws {
        let response: LoginResponse = try await APIClient.shared.request(
            path: "auth/login",
            payload: LoginRequest(email: email, password: password),
            responseType: LoginResponse.self
        )

        token = response.accessToken
        refreshToken = response.refreshToken
        userId = Self.extractUserId(fromJWT: response.accessToken)
        persistSession(token: response.accessToken, refreshToken: response.refreshToken, userId: userId)
    }

    func restoreSession() async {
        guard
            let tokenData = KeychainHelper.read(service: service, account: "token"),
            let token = String(data: tokenData, encoding: .utf8)
        else { return }

        self.token = token

        if let refreshData = KeychainHelper.read(service: service, account: "refreshToken"),
           let refresh = String(data: refreshData, encoding: .utf8) {
            self.refreshToken = refresh
        }

        if let userData = KeychainHelper.read(service: service, account: "userId"),
           let user = String(data: userData, encoding: .utf8) {
            self.userId = user
        } else {
            self.userId = Self.extractUserId(fromJWT: token)
        }
    }

    func logout() {
        token = nil
        userId = nil
        refreshToken = nil
        KeychainHelper.delete(service: service, account: "token")
        KeychainHelper.delete(service: service, account: "refreshToken")
        KeychainHelper.delete(service: service, account: "userId")
    }

    private func persistSession(token: String, refreshToken: String, userId: String?) {
        KeychainHelper.save(Data(token.utf8), service: service, account: "token")
        KeychainHelper.save(Data(refreshToken.utf8), service: service, account: "refreshToken")
        if let userId {
            KeychainHelper.save(Data(userId.utf8), service: service, account: "userId")
        }
    }

    private static func extractUserId(fromJWT token: String) -> String? {
        let parts = token.split(separator: ".")
        guard parts.count > 1 else { return nil }

        var payload = String(parts[1]).replacingOccurrences(of: "-", with: "+").replacingOccurrences(of: "_", with: "/")
        while payload.count % 4 != 0 {
            payload.append("=")
        }

        guard let payloadData = Data(base64Encoded: payload),
              let jsonObject = try? JSONSerialization.jsonObject(with: payloadData) as? [String: Any],
              let sub = jsonObject["sub"] as? String else {
            return nil
        }
        return sub
    }
}
