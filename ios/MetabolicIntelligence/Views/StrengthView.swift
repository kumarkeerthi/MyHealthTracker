import SwiftUI

struct StrengthView: View {
    var body: some View {
        NavigationStack {
            Text("Strength progression, volume, and readiness.")
                .modifier(CardStyle())
                .padding()
                .background(Color.black)
                .navigationTitle("Strength")
        }
    }
}
