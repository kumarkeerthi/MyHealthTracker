import SwiftUI

struct DashboardView: View {
    @EnvironmentObject private var authManager: AuthManager
    @StateObject private var viewModel = DashboardViewModel()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 12) {
                    if let summary = viewModel.summary {
                        Group {
                            Text("Calories: \(summary.calories)")
                            Text("Steps: \(summary.steps)")
                            Text("Resting HR: \(summary.restingHeartRate ?? 0, specifier: "%.1f")")
                            Text("HRV: \(summary.hrv ?? 0, specifier: "%.1f")")
                            Text("Sleep: \(summary.sleepHours ?? 0, specifier: "%.1f")h")
                        }
                        .modifier(CardStyle())
                    }

                    if let error = viewModel.error {
                        Text(error).foregroundStyle(.red)
                    }
                }
                .padding()
            }
            .background(Color.black)
            .navigationTitle("Dashboard")
            .task {
                if let token = authManager.token {
                    await viewModel.load(token: token)
                }
            }
        }
    }
}
