import Foundation

struct OfflineEvent: Codable, Identifiable {
    let id: UUID
    let endpoint: String
    let payload: Data
    let createdAt: Date
}

final class OfflineStore {
    static let shared = OfflineStore()

    private let fileURL: URL
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private let queue = DispatchQueue(label: "offline.store.queue")

    private init() {
        let root = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        fileURL = root.appendingPathComponent("pending-events.json")
        encoder.dateEncodingStrategy = .iso8601
        decoder.dateDecodingStrategy = .iso8601
    }

    func append(endpoint: String, payload: Data) {
        queue.sync {
            var events = load()
            events.append(OfflineEvent(id: UUID(), endpoint: endpoint, payload: payload, createdAt: Date()))
            save(events)
        }
    }

    func all() -> [OfflineEvent] {
        queue.sync { load() }
    }

    func remove(ids: Set<UUID>) {
        queue.sync {
            let filtered = load().filter { !ids.contains($0.id) }
            save(filtered)
        }
    }

    private func load() -> [OfflineEvent] {
        guard let data = try? Data(contentsOf: fileURL) else { return [] }
        return (try? decoder.decode([OfflineEvent].self, from: data)) ?? []
    }

    private func save(_ events: [OfflineEvent]) {
        let directory = fileURL.deletingLastPathComponent()
        try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        guard let data = try? encoder.encode(events) else { return }
        try? data.write(to: fileURL, options: .atomic)
    }
}
