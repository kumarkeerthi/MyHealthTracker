import SwiftUI

struct DashboardView: View {
    @EnvironmentObject private var authManager: AuthManager
    @EnvironmentObject private var healthKitManager: HealthKitManager
    @StateObject private var viewModel = DashboardViewModel()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 14) {
                    insulinScoreCard
                    macroProgressCard
                    movementCard

                    if let summary = viewModel.summary {
                        HStack(spacing: 10) {
                            metricChip(title: "Workouts", value: "\(summary.workouts)")
                            metricChip(title: "Steps", value: "\(summary.steps)")
                            metricChip(title: "Sleep", value: String(format: "%.1fh", summary.sleepHours ?? 0))
                        }
                    }

                    if let error = viewModel.error {
                        Text(error)
                            .foregroundStyle(.orange)
                            .font(.footnote)
                    }
                }
                .padding()
            }
            .background(Color.black.ignoresSafeArea())
            .navigationTitle("Home")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        Task { await healthKitManager.manualRefreshSync() }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                    .accessibilityLabel("Refresh health sync")
                }
            }
            .task {
                viewModel.bind(healthKitManager: healthKitManager)
                if let token = authManager.token {
                    await viewModel.load(token: token)
                }
            }
        }
    }

    private var insulinScoreCard: some View {
        VStack(spacing: 12) {
            ZStack {
                Circle()
                    .stroke(Color.white.opacity(0.1), lineWidth: 16)
                    .frame(width: 180, height: 180)
                Circle()
                    .trim(from: 0, to: viewModel.insulinLoadScore / 100)
                    .stroke(viewModel.insulinLoadScore < 40 ? Color.emerald : Color.orange, style: StrokeStyle(lineWidth: 16, lineCap: .round))
                    .rotationEffect(.degrees(-90))
                    .frame(width: 180, height: 180)
                    .shadow(color: viewModel.insulinLoadScore < 40 ? .emerald.opacity(0.9) : .clear, radius: 18)
                VStack(spacing: 2) {
                    Text("\(Int(viewModel.insulinLoadScore))")
                        .font(.system(size: 42, weight: .bold, design: .rounded))
                    Text("Insulin Load")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .modifier(CardStyle())
    }

    private var macroProgressCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Body Fuel")
                .font(.headline)
            ProgressRow(title: "Protein", value: viewModel.proteinProgress, color: .emerald)
            ProgressRow(title: "Carbs", value: viewModel.carbProgress, color: .blue)
            ProgressRow(title: "Oil", value: viewModel.oilProgress, color: .yellow)

            HStack {
                Text("Hydration")
                Spacer()
                ZStack {
                    Circle().stroke(Color.white.opacity(0.2), lineWidth: 7).frame(width: 42, height: 42)
                    Circle()
                        .trim(from: 0, to: viewModel.hydrationProgress)
                        .stroke(Color.cyan, style: StrokeStyle(lineWidth: 7, lineCap: .round))
                        .rotationEffect(.degrees(-90))
                        .frame(width: 42, height: 42)
                }
            }
        }
        .modifier(CardStyle())
    }

    private var movementCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Movement")
                .font(.headline)
            statRow("Post-meal walk", healthKitManager.latestSnapshot?.postMealWalkBonus == true ? "Completed" : "Pending")
            statRow("Step count", "\(healthKitManager.latestSnapshot?.steps ?? viewModel.summary?.steps ?? 0)")
            statRow("Walk streak", "5 days")
        }
        .modifier(CardStyle())
    }

    private func statRow(_ title: String, _ value: String) -> some View {
        HStack {
            Text(title).foregroundStyle(.secondary)
            Spacer()
            Text(value)
        }
        .font(.subheadline)
    }

    private func metricChip(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title).font(.caption).foregroundStyle(.secondary)
            Text(value).font(.headline)
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white.opacity(0.05), in: RoundedRectangle(cornerRadius: 12))
    }
}

private struct ProgressRow: View {
    let title: String
    let value: Double
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(title)
                Spacer()
                Text("\(Int(value * 100))%")
            }
            ProgressView(value: value)
                .tint(color)
        }
        .font(.subheadline)
    }
}
