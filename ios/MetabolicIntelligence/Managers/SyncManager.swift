import Foundation
import CryptoKit

@MainActor
final class SyncManager: ObservableObject {
    @Published private(set) var pendingCount: Int = 0

    private let encoder = JSONEncoder()
    private var syncTimestamps: [Date] = []

    private let signatureSecret = "CHANGE_ME_HEALTH_SYNC"

    init() {
        encoder.dateEncodingStrategy = .iso8601
        pendingCount = OfflineStore.shared.all().count
    }

    func enqueue<U: Encodable>(endpoint: String, payload: U) {
        guard let data = try? encoder.encode(payload) else { return }
        OfflineStore.shared.append(endpoint: endpoint, payload: data)
        pendingCount = OfflineStore.shared.all().count
    }

    func flushPendingIfNeeded(authManager: AuthManager) async {
        guard let token = authManager.token else { return }

        let events = OfflineStore.shared.all()
        var uploaded = Set<UUID>()
        for event in events {
            do {
                try await APIClient.shared.requestNoResponse(
                    path: event.endpoint,
                    token: token,
                    payload: RawPayload(data: event.payload)
                )
                uploaded.insert(event.id)
            } catch {
                break
            }
        }

        OfflineStore.shared.remove(ids: uploaded)
        pendingCount = OfflineStore.shared.all().count
    }

    func canSyncHealthDataNow() -> Bool {
        let now = Date()
        let oneHourAgo = now.addingTimeInterval(-3600)
        syncTimestamps = syncTimestamps.filter { $0 >= oneHourAgo }
        return syncTimestamps.count < 10
    }

    func markSyncPerformed() {
        syncTimestamps.append(Date())
    }

    func signedHeaders(for body: Data) -> [String: String] {
        let timestamp = Int(Date().timeIntervalSince1970)
        let prefix = "\(timestamp).".data(using: .utf8) ?? Data()
        let signatureBytes = HMAC<SHA256>.authenticationCode(for: prefix + body, using: SymmetricKey(data: Data(signatureSecret.utf8)))
        let signature = Data(signatureBytes).map { String(format: "%02x", $0) }.joined()
        return [
            "X-Sync-Timestamp": "\(timestamp)",
            "X-Sync-Signature": signature
        ]
    }
}

private struct RawPayload: Encodable {
    let data: Data

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        let object = try JSONSerialization.jsonObject(with: data)
        try container.encode(AnyCodable(object))
    }
}

private struct AnyCodable: Encodable {
    private let value: Any

    init(_ value: Any) {
        self.value = value
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch value {
        case let v as String: try container.encode(v)
        case let v as Int: try container.encode(v)
        case let v as Double: try container.encode(v)
        case let v as Bool: try container.encode(v)
        case let v as [String: Any]:
            try container.encode(v.mapValues { AnyCodable($0) })
        case let v as [Any]:
            try container.encode(v.map { AnyCodable($0) })
        default:
            try container.encodeNil()
        }
    }
}
