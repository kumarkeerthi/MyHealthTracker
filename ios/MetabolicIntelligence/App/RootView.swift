import SwiftUI

struct RootView: View {
    @EnvironmentObject private var authManager: AuthManager

    var body: some View {
        Group {
            if authManager.isAuthenticated {
                DashboardTabView()
            } else {
                LoginView()
            }
        }
    }
}

#Preview {
    RootView()
        .environmentObject(AuthManager())
}
