import Foundation

struct LoginRequest: Encodable {
    let email: String
    let password: String
}

struct LoginResponse: Decodable {
    let accessToken: String
    let userId: String
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

struct AnalyzeFoodImageResponse: Decodable {
    let foods: [String]
    let caloriesEstimate: Int?
    let confidence: Double
}

struct PushSubscribePayload: Encodable {
    let deviceToken: String
    let platform: String
}
