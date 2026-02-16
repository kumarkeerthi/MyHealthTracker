import SwiftUI

struct DashboardTabView: View {
    var body: some View {
        TabView {
            DashboardView()
                .tabItem { Label("Home", systemImage: "house") }
            BodyView()
                .tabItem { Label("Body", systemImage: "figure.stand") }
            StrengthView()
                .tabItem { Label("Strength", systemImage: "figure.strengthtraining.traditional") }
            AnalyticsView()
                .tabItem { Label("Analytics", systemImage: "chart.line.uptrend.xyaxis") }
            ProfileView()
                .tabItem { Label("Profile", systemImage: "person") }
        }
        .tint(.emerald)
    }
}
