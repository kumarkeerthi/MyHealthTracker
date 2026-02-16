import Foundation

@MainActor
final class DashboardViewModel: ObservableObject {
    @Published var summary: DailySummary?
    @Published var isLoading = false
    @Published var error: String?

    func load(token: String) async {
        isLoading = true
        defer { isLoading = false }

        do {
            struct EmptyPayload: Encodable {}
            let response: DailySummary = try await APIClient.shared.request(
                path: "daily-summary",
                method: "GET",
                token: token,
                payload: Optional<EmptyPayload>.none,
                responseType: DailySummary.self
            )
            summary = response
        } catch {
            self.error = error.localizedDescription
        }
    }
}
