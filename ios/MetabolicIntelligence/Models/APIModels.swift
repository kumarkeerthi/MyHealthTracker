import Foundation

struct LoginRequest: Encodable {
    let email: String
    let password: String
}

struct LoginResponse: Decodable {
    let accessToken: String
    let refreshToken: String
    let tokenType: String
    let expiresInSeconds: Int

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case tokenType = "token_type"
        case expiresInSeconds = "expires_in_seconds"
    }
}

struct DailySummary: Decodable {
    let date: String
    let calories: Int
    let steps: Int
    let restingHeartRate: Double?
    let hrv: Double?
    let sleepHours: Double?
    let workouts: Int
}

struct HealthSnapshot: Codable {
    let steps: Int
    let restingHeartRate: Double?
    let hrv: Double?
    let sleepHours: Double
    let vo2Max: Double?
    let postMealWalkBonus: Bool
    let capturedAt: Date
}

struct FoodLogPayload: Codable {
    let mealType: String
    let foods: [String]
    let calories: Int?
    let eatenAt: Date
}

struct VitalsPayload: Codable {
    let restingHeartRate: Double?
    let hrv: Double?
    let sleepHours: Double?
    let steps: Int?
    let capturedAt: Date
}

struct ExercisePayload: Codable {
    let workoutType: String
    let durationMinutes: Int
    let caloriesBurned: Double?
    let startedAt: Date
    let isPostMealWalk: Bool
}

struct AppleSyncBatchPayload: Codable {
    let vitals: VitalsPayload
    let exercise: ExercisePayload?
    let snapshot: HealthSnapshot
}

struct StrengthSnapshot {
    let strengthIndex: Double
    let gripStrengthKg: Double
    let pullUps: Int
    let deadHangSeconds: Int
    let pushUps: Int
}

struct AnalyzeFoodImageResponse: Decodable {
    let foods: [String]
    let caloriesEstimate: Int?
    let confidence: Double
}

struct PushSubscribePayload: Encodable {
    let deviceToken: String
    let platform: String
}
