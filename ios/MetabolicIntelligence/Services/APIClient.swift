import Foundation

enum APIError: LocalizedError {
    case invalidResponse
    case httpError(Int)
    case decodingFailed

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "Invalid server response"
        case .httpError(let code):
            return "Request failed with status code \(code)"
        case .decodingFailed:
            return "Could not decode server response"
        }
    }
}

final class APIClient {
    static let shared = APIClient()

    private let session: URLSession
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private let baseURL = URL(string: "https://api.metabolic-intelligence.com")!

    private init() {
        let config = URLSessionConfiguration.default
        config.waitsForConnectivity = true
        session = URLSession(configuration: config)
        encoder.dateEncodingStrategy = .iso8601
        decoder.dateDecodingStrategy = .iso8601
    }

    func request<T: Decodable, U: Encodable>(
        path: String,
        method: String = "POST",
        token: String? = nil,
        payload: U? = nil,
        extraHeaders: [String: String] = [:],
        responseType: T.Type
    ) async throws -> T {
        let data = try await dataRequest(path: path, method: method, token: token, payload: payload, extraHeaders: extraHeaders)
        guard !data.isEmpty else { throw APIError.decodingFailed }
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingFailed
        }
    }

    func requestNoResponse<U: Encodable>(
        path: String,
        method: String = "POST",
        token: String? = nil,
        payload: U? = nil,
        extraHeaders: [String: String] = [:]
    ) async throws {
        _ = try await dataRequest(path: path, method: method, token: token, payload: payload, extraHeaders: extraHeaders)
    }

    func uploadImage(
        path: String,
        token: String,
        imageData: Data,
        mimeType: String = "image/jpeg"
    ) async throws -> AnalyzeFoodImageResponse {
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = "POST"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")

        let boundary = UUID().uuidString
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"food.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: \(mimeType)\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

        request.httpBody = body

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw APIError.invalidResponse }
        guard (200...299).contains(http.statusCode) else { throw APIError.httpError(http.statusCode) }
        return try decoder.decode(AnalyzeFoodImageResponse.self, from: data)
    }

    private func dataRequest<U: Encodable>(
        path: String,
        method: String,
        token: String?,
        payload: U?,
        extraHeaders: [String: String] = [:]
    ) async throws -> Data {
        var request = URLRequest(url: baseURL.appendingPathComponent(path))
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        for (key, value) in extraHeaders {
            request.setValue(value, forHTTPHeaderField: key)
        }
        if let payload {
            request.httpBody = try encoder.encode(payload)
        }

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw APIError.invalidResponse }
        guard (200...299).contains(http.statusCode) else { throw APIError.httpError(http.statusCode) }
        return data
    }
}
