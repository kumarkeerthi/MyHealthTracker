import SwiftUI

struct AnalyticsView: View {
    var body: some View {
        NavigationStack {
            Text("Metabolic analytics and trend visualization.")
                .modifier(CardStyle())
                .padding()
                .background(Color.black)
                .navigationTitle("Analytics")
        }
    }
}
