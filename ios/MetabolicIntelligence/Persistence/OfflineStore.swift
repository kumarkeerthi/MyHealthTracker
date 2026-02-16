import Foundation

struct OfflineEvent: Codable, Identifiable {
    let id: UUID
    let endpoint: String
    let payload: Data
    let createdAt: Date
}

final class OfflineStore {
    static let shared = OfflineStore()

    private let eventsURL: URL
    private let summaryURL: URL
    private let vitalsURL: URL
    private let encoder = JSONEncoder()
    private let decoder = JSONDecoder()
    private let queue = DispatchQueue(label: "offline.store.queue")

    private init() {
        let root = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
        eventsURL = root.appendingPathComponent("pending-events.json")
        summaryURL = root.appendingPathComponent("last-daily-summary.json")
        vitalsURL = root.appendingPathComponent("last-vitals.json")
        encoder.dateEncodingStrategy = .iso8601
        decoder.dateDecodingStrategy = .iso8601
    }

    func append(endpoint: String, payload: Data) {
        queue.sync {
            var events = loadEvents()
            events.append(OfflineEvent(id: UUID(), endpoint: endpoint, payload: payload, createdAt: Date()))
            save(events)
        }
    }

    func all() -> [OfflineEvent] {
        queue.sync { loadEvents() }
    }

    func remove(ids: Set<UUID>) {
        queue.sync {
            let filtered = loadEvents().filter { !ids.contains($0.id) }
            save(filtered)
        }
    }

    func saveLastDailySummary(_ summary: DailySummary) {
        queue.sync {
            saveObject(summary, to: summaryURL)
        }
    }

    func loadLastDailySummary() -> DailySummary? {
        queue.sync {
            loadObject(from: summaryURL)
        }
    }

    func saveLastVitals(_ vitals: VitalsPayload) {
        queue.sync {
            saveObject(vitals, to: vitalsURL)
        }
    }

    func loadLastVitals() -> VitalsPayload? {
        queue.sync {
            loadObject(from: vitalsURL)
        }
    }

    private func loadEvents() -> [OfflineEvent] {
        guard let data = try? Data(contentsOf: eventsURL) else { return [] }
        return (try? decoder.decode([OfflineEvent].self, from: data)) ?? []
    }

    private func save(_ events: [OfflineEvent]) {
        saveObject(events, to: eventsURL)
    }

    private func saveObject<T: Encodable>(_ object: T, to fileURL: URL) {
        let directory = fileURL.deletingLastPathComponent()
        try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        guard let data = try? encoder.encode(object) else { return }
        try? data.write(to: fileURL, options: .atomic)
    }

    private func loadObject<T: Decodable>(from fileURL: URL) -> T? {
        guard let data = try? Data(contentsOf: fileURL) else { return nil }
        return try? decoder.decode(T.self, from: data)
    }
}
