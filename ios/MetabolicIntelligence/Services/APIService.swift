import Foundation

@MainActor
final class APIService {
    static let shared = APIService()

    private init() {}

    func fetchDailySummary(token: String) async throws -> DailySummary {
        struct EmptyPayload: Encodable {}
        return try await APIClient.shared.request(
            path: "daily-summary",
            method: "GET",
            token: token,
            payload: Optional<EmptyPayload>.none,
            responseType: DailySummary.self
        )
    }

    func logVitals(token: String, payload: VitalsPayload) async throws {
        try await APIClient.shared.requestNoResponse(path: "log-vitals", token: token, payload: payload)
    }

    func logExercise(token: String, payload: ExercisePayload) async throws {
        try await APIClient.shared.requestNoResponse(path: "log-exercise", token: token, payload: payload)
    }

    func syncAppleHealth(token: String, payload: AppleSyncBatchPayload) async throws {
        try await APIClient.shared.requestNoResponse(path: "apple-sync", token: token, payload: payload)
    }
}
