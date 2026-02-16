import SwiftUI

struct BodyView: View {
    var body: some View {
        NavigationStack {
            Text("Body composition, vitals trends, and recovery signals.")
                .modifier(CardStyle())
                .padding()
                .background(Color.black)
                .navigationTitle("Body")
        }
    }
}
