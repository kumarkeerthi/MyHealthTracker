import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var authManager: AuthManager
    @State private var email = ""
    @State private var password = ""
    @State private var error: String?

    var body: some View {
        NavigationStack {
            ZStack {
                Color.black.ignoresSafeArea()
                VStack(spacing: 20) {
                    Text("Metabolic Intelligence")
                        .font(.largeTitle.bold())
                        .foregroundStyle(.white)

                    TextField("Email", text: $email)
                        .textInputAutocapitalization(.never)
                        .padding()
                        .background(.gray.opacity(0.2), in: RoundedRectangle(cornerRadius: 12))

                    SecureField("Password", text: $password)
                        .padding()
                        .background(.gray.opacity(0.2), in: RoundedRectangle(cornerRadius: 12))

                    if let error {
                        Text(error).foregroundStyle(.red)
                    }

                    Button("Login") {
                        Task {
                            do {
                                try await authManager.login(email: email, password: password)
                            } catch {
                                self.error = error.localizedDescription
                            }
                        }
                    }
                    .buttonStyle(EmeraldButtonStyle())
                }
                .padding()
            }
        }
    }
}
