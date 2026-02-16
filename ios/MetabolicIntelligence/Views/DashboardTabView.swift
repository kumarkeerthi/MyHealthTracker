import SwiftUI

struct DashboardTabView: View {
    var body: some View {
        TabView {
            DashboardView()
                .tabItem { Label("Dashboard", systemImage: "house") }
            BodyView()
                .tabItem { Label("Body", systemImage: "heart.text.square") }
            StrengthView()
                .tabItem { Label("Strength", systemImage: "figure.strengthtraining.traditional") }
            AnalyticsView()
                .tabItem { Label("Analytics", systemImage: "chart.line.uptrend.xyaxis") }
            ProfileView()
                .tabItem { Label("Profile", systemImage: "person") }
            ScanFoodView()
                .tabItem { Label("Scan", systemImage: "camera") }
            SettingsView()
                .tabItem { Label("Settings", systemImage: "gearshape") }
        }
        .tint(.emerald)
    }
}
