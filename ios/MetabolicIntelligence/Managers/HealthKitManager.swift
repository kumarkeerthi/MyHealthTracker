import Foundation
import HealthKit

@MainActor
final class HealthKitManager: ObservableObject {
    @Published var isAuthorized = false

    private let healthStore = HKHealthStore()
    private var authManager: AuthManager?
    private var syncManager: SyncManager?

    func bootstrap(authManager: AuthManager, syncManager: SyncManager) async {
        self.authManager = authManager
        self.syncManager = syncManager
        guard HKHealthStore.isHealthDataAvailable() else { return }
        await requestAuthorization()
        if isAuthorized {
            await syncDailyVitals()
            enableWorkoutObserver()
        }
    }

    func requestAuthorization() async {
        let readTypes: Set<HKObjectType> = [
            HKObjectType.quantityType(forIdentifier: .stepCount),
            HKObjectType.quantityType(forIdentifier: .restingHeartRate),
            HKObjectType.categoryType(forIdentifier: .sleepAnalysis),
            HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN),
            HKObjectType.workoutType()
        ]
        .compactMap { $0 }

        do {
            try await healthStore.requestAuthorization(toShare: [], read: readTypes)
            isAuthorized = true
        } catch {
            isAuthorized = false
        }
    }

    func syncDailyVitals() async {
        guard let token = authManager?.token else { return }

        let steps = await todayStepCount()
        let resting = await todayAverage(for: .restingHeartRate, unit: HKUnit.count().unitDivided(by: .minute()))
        let hrv = await todayAverage(for: .heartRateVariabilitySDNN, unit: .secondUnit(with: .milli))
        let sleep = await todaySleepHours()

        let payload = VitalsPayload(
            restingHeartRate: resting,
            hrv: hrv,
            sleepHours: sleep,
            steps: Int(steps),
            capturedAt: Date()
        )

        do {
            try await APIClient.shared.requestNoResponse(path: "log-vitals", token: token, payload: payload)
        } catch {
            syncManager?.enqueue(endpoint: "log-vitals", payload: payload)
        }
    }

    private func enableWorkoutObserver() {
        let workoutType = HKObjectType.workoutType()
        let query = HKObserverQuery(sampleType: workoutType, predicate: nil) { [weak self] _, _, _ in
            Task { await self?.handleLatestWorkout() }
        }
        healthStore.execute(query)
    }

    private func handleLatestWorkout() async {
        guard let token = authManager?.token else { return }
        let predicate = HKQuery.predicateForSamples(withStart: Calendar.current.date(byAdding: .day, value: -1, to: Date()), end: Date())

        let sort = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)
        let latest: HKWorkout? = await withCheckedContinuation { continuation in
            let query = HKSampleQuery(sampleType: .workoutType(), predicate: predicate, limit: 1, sortDescriptors: [sort]) { _, samples, _ in
                continuation.resume(returning: samples?.first as? HKWorkout)
            }
            healthStore.execute(query)
        }

        guard let workout = latest else { return }
        let mealDate = UserDefaults.standard.object(forKey: "lastMealDate") as? Date
        let isPostMealWalk = workout.workoutActivityType == .walking && mealDate.map { workout.startDate.timeIntervalSince($0) < 90 * 60 } == true

        let payload = ExercisePayload(
            workoutType: workout.workoutActivityType.name,
            durationMinutes: Int(workout.duration / 60),
            caloriesBurned: workout.totalEnergyBurned?.doubleValue(for: .kilocalorie()),
            startedAt: workout.startDate,
            isPostMealWalk: isPostMealWalk
        )

        do {
            try await APIClient.shared.requestNoResponse(path: "log-exercise", token: token, payload: payload)
        } catch {
            syncManager?.enqueue(endpoint: "log-exercise", payload: payload)
        }
    }

    private func todayStepCount() async -> Double {
        await todaySum(for: .stepCount, unit: .count())
    }

    private func todayAverage(for identifier: HKQuantityTypeIdentifier, unit: HKUnit) async -> Double? {
        guard let type = HKObjectType.quantityType(forIdentifier: identifier) else { return nil }
        let predicate = HKQuery.predicateForSamples(withStart: Calendar.current.startOfDay(for: Date()), end: Date())

        return await withCheckedContinuation { continuation in
            let query = HKStatisticsQuery(quantityType: type, quantitySamplePredicate: predicate, options: .discreteAverage) { _, stats, _ in
                continuation.resume(returning: stats?.averageQuantity()?.doubleValue(for: unit))
            }
            healthStore.execute(query)
        }
    }

    private func todaySum(for identifier: HKQuantityTypeIdentifier, unit: HKUnit) async -> Double {
        guard let type = HKObjectType.quantityType(forIdentifier: identifier) else { return 0 }
        let predicate = HKQuery.predicateForSamples(withStart: Calendar.current.startOfDay(for: Date()), end: Date())

        return await withCheckedContinuation { continuation in
            let query = HKStatisticsQuery(quantityType: type, quantitySamplePredicate: predicate, options: .cumulativeSum) { _, stats, _ in
                continuation.resume(returning: stats?.sumQuantity()?.doubleValue(for: unit) ?? 0)
            }
            healthStore.execute(query)
        }
    }

    private func todaySleepHours() async -> Double {
        guard let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else { return 0 }
        let predicate = HKQuery.predicateForSamples(withStart: Calendar.current.startOfDay(for: Date()), end: Date())
        return await withCheckedContinuation { continuation in
            let query = HKSampleQuery(sampleType: sleepType, predicate: predicate, limit: HKObjectQueryNoLimit, sortDescriptors: nil) { _, samples, _ in
                let duration = (samples as? [HKCategorySample] ?? [])
                    .filter { $0.value == HKCategoryValueSleepAnalysis.asleepUnspecified.rawValue }
                    .reduce(0.0) { $0 + $1.endDate.timeIntervalSince($1.startDate) }
                continuation.resume(returning: duration / 3600.0)
            }
            healthStore.execute(query)
        }
    }
}

private extension HKWorkoutActivityType {
    var name: String {
        switch self {
        case .walking: return "walking"
        case .running: return "running"
        case .traditionalStrengthTraining: return "strength"
        default: return "other"
        }
    }
}
