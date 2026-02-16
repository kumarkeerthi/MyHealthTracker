import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var authManager: AuthManager
    @EnvironmentObject private var healthKitManager: HealthKitManager
    @EnvironmentObject private var syncManager: SyncManager
    @State private var status = ""

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                Toggle("HealthKit Authorized", isOn: .constant(healthKitManager.isAuthorized))
                    .disabled(true)
                    .modifier(CardStyle())

                Text("Pending Offline Events: \(syncManager.pendingCount)")
                    .modifier(CardStyle())

                Button("Sync Health Data Now") {
                    Task {
                        await healthKitManager.syncDailyVitals()
                        status = "Sync requested"
                    }
                }
                .buttonStyle(EmeraldButtonStyle())

                Button("Flush Offline Queue") {
                    Task {
                        await syncManager.flushPendingIfNeeded(authManager: authManager)
                        status = "Queue flushed"
                    }
                }
                .buttonStyle(EmeraldButtonStyle())

                if !status.isEmpty { Text(status).foregroundStyle(.emerald) }
            }
            .padding()
            .background(Color.black)
            .navigationTitle("Settings")
        }
    }
}
