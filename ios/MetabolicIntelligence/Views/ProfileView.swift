import SwiftUI

struct ProfileView: View {
    @EnvironmentObject private var authManager: AuthManager

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                Text("User ID: \(authManager.userId ?? "-")")
                    .modifier(CardStyle())

                Button("Logout") {
                    authManager.logout()
                }
                .buttonStyle(EmeraldButtonStyle())
            }
            .padding()
            .background(Color.black)
            .navigationTitle("Profile")
        }
    }
}
