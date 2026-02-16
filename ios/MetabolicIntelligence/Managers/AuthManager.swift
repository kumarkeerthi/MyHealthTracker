import Foundation

@MainActor
final class AuthManager: ObservableObject {
    @Published private(set) var token: String?
    @Published private(set) var userId: String?

    var isAuthenticated: Bool { token != nil }

    private let service = "com.metabolicintelligence.auth"

    func login(email: String, password: String) async throws {
        let response: LoginResponse = try await APIClient.shared.request(
            path: "login",
            payload: LoginRequest(email: email, password: password),
            responseType: LoginResponse.self
        )

        token = response.accessToken
        userId = response.userId
        persistSession(token: response.accessToken, userId: response.userId)
    }

    func restoreSession() async {
        guard
            let tokenData = KeychainHelper.read(service: service, account: "token"),
            let userData = KeychainHelper.read(service: service, account: "userId"),
            let token = String(data: tokenData, encoding: .utf8),
            let user = String(data: userData, encoding: .utf8)
        else { return }

        self.token = token
        self.userId = user
    }

    func logout() {
        token = nil
        userId = nil
        KeychainHelper.delete(service: service, account: "token")
        KeychainHelper.delete(service: service, account: "userId")
    }

    private func persistSession(token: String, userId: String) {
        KeychainHelper.save(Data(token.utf8), service: service, account: "token")
        KeychainHelper.save(Data(userId.utf8), service: service, account: "userId")
    }
}
