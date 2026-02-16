import Foundation
import Combine

@MainActor
final class DashboardViewModel: ObservableObject {
    @Published var summary: DailySummary?
    @Published var insulinLoadScore: Double = 52
    @Published var proteinProgress: Double = 0.64
    @Published var carbProgress: Double = 0.47
    @Published var oilProgress: Double = 0.36
    @Published var hydrationProgress: Double = 0.71
    @Published var isLoading = false
    @Published var error: String?

    private var cancellables = Set<AnyCancellable>()

    func bind(healthKitManager: HealthKitManager) {
        healthKitManager.$latestSnapshot
            .compactMap { $0 }
            .receive(on: DispatchQueue.main)
            .sink { [weak self] snapshot in
                guard let self else { return }
                if snapshot.postMealWalkBonus {
                    self.insulinLoadScore = max(25, self.insulinLoadScore - 6)
                }
                self.hydrationProgress = min(1.0, max(self.hydrationProgress, snapshot.sleepHours >= 7 ? 0.75 : self.hydrationProgress))
            }
            .store(in: &cancellables)
    }

    func load(token: String) async {
        isLoading = true
        defer { isLoading = false }

        do {
            let response = try await APIService.shared.fetchDailySummary(token: token)
            summary = response
            OfflineStore.shared.saveLastDailySummary(response)
        } catch {
            self.error = error.localizedDescription
            self.summary = OfflineStore.shared.loadLastDailySummary()
        }
    }
}
