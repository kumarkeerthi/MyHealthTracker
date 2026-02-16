import Foundation
import HealthKit

@MainActor
final class HealthKitManager: ObservableObject {
    @Published private(set) var isAuthorized = false
    @Published private(set) var latestSnapshot: HealthSnapshot?

    private let healthStore = HKHealthStore()
    private var authManager: AuthManager?
    private var syncManager: SyncManager?
    private var midnightTimer: Timer?
    private var midnightTimerProxy: TimerProxy?

    func bootstrap(authManager: AuthManager, syncManager: SyncManager) async {
        self.authManager = authManager
        self.syncManager = syncManager

        guard HKHealthStore.isHealthDataAvailable() else { return }
        await requestPermissions()
        guard isAuthorized else { return }

        await syncDailyVitals(trigger: .midnight)
        enableWorkoutObserver()
        scheduleDailyMidnightSync()
    }

    func requestPermissions() async {
        let readTypes: Set<HKObjectType> = [
            HKObjectType.quantityType(forIdentifier: .stepCount),
            HKObjectType.quantityType(forIdentifier: .restingHeartRate),
            HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN),
            HKObjectType.categoryType(forIdentifier: .sleepAnalysis),
            HKObjectType.quantityType(forIdentifier: .vo2Max),
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

    func fetchDailySteps() async -> Int {
        Int(await todaySum(for: .stepCount, unit: .count()))
    }

    func fetchRestingHR() async -> Double? {
        await todayAverage(for: .restingHeartRate, unit: HKUnit.count().unitDivided(by: .minute()))
    }

    func fetchSleepHours() async -> Double {
        guard let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else { return 0 }
        let dayStart = Calendar.current.startOfDay(for: Date())
        let predicate = HKQuery.predicateForSamples(withStart: dayStart, end: Date())

        return await withCheckedContinuation { continuation in
            let query = HKSampleQuery(sampleType: sleepType, predicate: predicate, limit: HKObjectQueryNoLimit, sortDescriptors: nil) { _, samples, _ in
                let asleepValues: Set<Int> = [
                    HKCategoryValueSleepAnalysis.asleepCore.rawValue,
                    HKCategoryValueSleepAnalysis.asleepDeep.rawValue,
                    HKCategoryValueSleepAnalysis.asleepREM.rawValue,
                    HKCategoryValueSleepAnalysis.asleepUnspecified.rawValue
                ]

                let duration = (samples as? [HKCategorySample] ?? [])
                    .filter { asleepValues.contains($0.value) }
                    .reduce(0.0) { $0 + $1.endDate.timeIntervalSince($1.startDate) }

                continuation.resume(returning: duration / 3600.0)
            }
            healthStore.execute(query)
        }
    }

    func fetchWorkouts(since startDate: Date = Calendar.current.date(byAdding: .day, value: -1, to: Date()) ?? Date()) async -> [HKWorkout] {
        let predicate = HKQuery.predicateForSamples(withStart: startDate, end: Date())
        let sort = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)

        return await withCheckedContinuation { continuation in
            let query = HKSampleQuery(sampleType: .workoutType(), predicate: predicate, limit: HKObjectQueryNoLimit, sortDescriptors: [sort]) { _, samples, _ in
                continuation.resume(returning: samples as? [HKWorkout] ?? [])
            }
            healthStore.execute(query)
        }
    }

    func detectPostMealWalk() async -> Bool {
        let mealDate = UserDefaults.standard.object(forKey: "lastMealDate") as? Date
        guard let mealDate else { return false }

        let windowEnd = Calendar.current.date(byAdding: .minute, value: 60, to: mealDate) ?? mealDate
        guard windowEnd > mealDate else { return false }

        let workouts = await fetchWorkouts(since: mealDate)
        let walkWorkoutFound = workouts.contains {
            $0.workoutActivityType == .walking && $0.startDate >= mealDate && $0.startDate <= windowEnd
        }
        if walkWorkoutFound { return true }

        let baselineStart = Calendar.current.date(byAdding: .minute, value: -60, to: mealDate) ?? mealDate
        let baselineSteps = await stepSum(from: baselineStart, to: mealDate)
        let postMealSteps = await stepSum(from: mealDate, to: windowEnd)
        return postMealSteps >= max(350, baselineSteps * 1.5)
    }

    func syncDailyVitals(trigger: SyncTrigger = .manual) async {
        _ = trigger
        guard let token = authManager?.token else { return }
        guard let syncManager else { return }
        guard syncManager.canSyncHealthDataNow() else { return }

        let steps = await fetchDailySteps()
        let resting = await fetchRestingHR()
        let hrv = await todayAverage(for: .heartRateVariabilitySDNN, unit: .secondUnit(with: .milli))
        let sleep = await fetchSleepHours()
        let vo2Max = await todayAverage(for: .vo2Max, unit: HKUnit(from: "ml/kg*min"))
        let workouts = await fetchWorkouts()
        let postMealWalkBonus = await detectPostMealWalk()

        let vitalsPayload = VitalsPayload(
            restingHeartRate: resting,
            hrv: hrv,
            sleepHours: sleep,
            steps: steps,
            capturedAt: Date()
        )

        let latestWorkout = workouts.first
        let exercisePayload = latestWorkout.map {
            ExercisePayload(
                workoutType: $0.workoutActivityType.name,
                durationMinutes: Int($0.duration / 60),
                caloriesBurned: $0.totalEnergyBurned?.doubleValue(for: .kilocalorie()),
                startedAt: $0.startDate,
                isPostMealWalk: postMealWalkBonus
            )
        }

        let snapshot = HealthSnapshot(
            steps: steps,
            restingHeartRate: resting,
            hrv: hrv,
            sleepHours: sleep,
            vo2Max: vo2Max,
            postMealWalkBonus: postMealWalkBonus,
            capturedAt: Date()
        )

        latestSnapshot = snapshot
        OfflineStore.shared.saveLastVitals(vitalsPayload)

        let dateKey = ISO8601DateFormatter.healthSyncDateOnly.string(from: Date())
        let summaryPayload = HealthSummarySyncPayload(
            date: dateKey,
            steps: steps,
            restingHR: resting,
            sleepHours: sleep,
            hrv: hrv,
            workouts: workouts.map {
                HealthSyncWorkoutPayload(
                    type: $0.workoutActivityType.name,
                    duration: Int($0.duration / 60),
                    calories: $0.totalEnergyBurned?.doubleValue(for: .kilocalorie()),
                    startTime: $0.startDate
                )
            },
            generatedAt: Date()
        )

        do {
            try await APIClient.shared.requestNoResponse(path: "log-vitals", token: token, payload: vitalsPayload)

            if let exercisePayload {
                try await APIClient.shared.requestNoResponse(path: "log-exercise", token: token, payload: exercisePayload)
            }

            let applePayload = AppleSyncBatchPayload(vitals: vitalsPayload, exercise: exercisePayload, snapshot: snapshot)
            try await APIClient.shared.requestNoResponse(path: "apple-sync", token: token, payload: applePayload)

            let summaryBody = try encoder.encode(summaryPayload)
            try await APIClient.shared.requestNoResponse(
                path: "health/sync-summary",
                token: token,
                payload: summaryPayload,
                extraHeaders: syncManager.signedHeaders(for: summaryBody)
            )
            syncManager.markSyncPerformed()
        } catch {
            syncManager?.enqueue(endpoint: "log-vitals", payload: vitalsPayload)
            if let exercisePayload {
                syncManager?.enqueue(endpoint: "log-exercise", payload: exercisePayload)
            }
            let applePayload = AppleSyncBatchPayload(vitals: vitalsPayload, exercise: exercisePayload, snapshot: snapshot)
            syncManager?.enqueue(endpoint: "apple-sync", payload: applePayload)
            syncManager?.enqueue(endpoint: "health/sync-summary", payload: summaryPayload)
        }
    }

    private func enableWorkoutObserver() {
        let workoutType = HKObjectType.workoutType()
        let query = HKObserverQuery(sampleType: workoutType, predicate: nil) { [weak self] _, _, _ in
            Task { await self?.syncDailyVitals(trigger: .workout) }
        }
        healthStore.execute(query)
    }



    func manualRefreshSync() async {
        await syncDailyVitals(trigger: .manual)
    }

    private func scheduleDailyMidnightSync() {
        midnightTimer?.invalidate()
        let nextMidnight = Calendar.current.nextDate(after: Date(), matching: DateComponents(hour: 0, minute: 0, second: 5), matchingPolicy: .nextTime) ?? Date().addingTimeInterval(3600)
        midnightTimerProxy = TimerProxy { [weak self] in
            Task { await self?.syncDailyVitals(trigger: .midnight) }
        }
        guard let midnightTimerProxy else { return }
        midnightTimer = Timer(fireAt: nextMidnight, interval: 86400, target: midnightTimerProxy, selector: #selector(TimerProxy.fire), userInfo: nil, repeats: true)
        if let timer = midnightTimer {
            RunLoop.main.add(timer, forMode: .common)
        }
    }

    private func todayAverage(for identifier: HKQuantityTypeIdentifier, unit: HKUnit) async -> Double? {
        guard let type = HKObjectType.quantityType(forIdentifier: identifier) else { return nil }
        return await average(for: type, unit: unit, from: Calendar.current.startOfDay(for: Date()), to: Date())
    }

    private func todaySum(for identifier: HKQuantityTypeIdentifier, unit: HKUnit) async -> Double {
        guard let type = HKObjectType.quantityType(forIdentifier: identifier) else { return 0 }
        return await sum(for: type, unit: unit, from: Calendar.current.startOfDay(for: Date()), to: Date())
    }

    private func stepSum(from startDate: Date, to endDate: Date) async -> Double {
        guard let type = HKObjectType.quantityType(forIdentifier: .stepCount) else { return 0 }
        return await sum(for: type, unit: .count(), from: startDate, to: endDate)
    }

    private func average(for type: HKQuantityType, unit: HKUnit, from startDate: Date, to endDate: Date) async -> Double? {
        let predicate = HKQuery.predicateForSamples(withStart: startDate, end: endDate)

        return await withCheckedContinuation { continuation in
            let query = HKStatisticsQuery(quantityType: type, quantitySamplePredicate: predicate, options: .discreteAverage) { _, stats, _ in
                continuation.resume(returning: stats?.averageQuantity()?.doubleValue(for: unit))
            }
            healthStore.execute(query)
        }
    }

    private func sum(for type: HKQuantityType, unit: HKUnit, from startDate: Date, to endDate: Date) async -> Double {
        let predicate = HKQuery.predicateForSamples(withStart: startDate, end: endDate)

        return await withCheckedContinuation { continuation in
            let query = HKStatisticsQuery(quantityType: type, quantitySamplePredicate: predicate, options: .cumulativeSum) { _, stats, _ in
                continuation.resume(returning: stats?.sumQuantity()?.doubleValue(for: unit) ?? 0)
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


private enum SyncTrigger {
    case midnight
    case workout
    case manual
}

private final class TimerProxy: NSObject {
    private let callback: () -> Void

    init(callback: @escaping () -> Void) {
        self.callback = callback
    }

    @objc func fire() {
        callback()
    }
}

private extension ISO8601DateFormatter {
    static let healthSyncDateOnly: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withFullDate]
        return formatter
    }()
}
