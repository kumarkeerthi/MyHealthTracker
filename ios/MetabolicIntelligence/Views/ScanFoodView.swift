import SwiftUI

struct ScanFoodView: View {
    @EnvironmentObject private var authManager: AuthManager
    @EnvironmentObject private var syncManager: SyncManager
    @State private var showCamera = false
    @State private var image: UIImage?
    @State private var analysis: AnalyzeFoodImageResponse?
    @State private var error: String?

    var body: some View {
        NavigationStack {
            VStack(spacing: 16) {
                if let image {
                    Image(uiImage: image)
                        .resizable()
                        .scaledToFit()
                        .frame(maxHeight: 240)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                }

                Button("Open Camera") { showCamera = true }
                    .buttonStyle(EmeraldButtonStyle())

                if let analysis {
                    Text("Detected: \(analysis.foods.joined(separator: ", "))")
                    Text("Calories: \(analysis.caloriesEstimate ?? 0)")
                    Button("Log Meal") { Task { await logMeal(from: analysis) } }
                        .buttonStyle(EmeraldButtonStyle())
                }

                if let error { Text(error).foregroundStyle(.red) }
                Spacer()
            }
            .padding()
            .background(Color.black)
            .navigationTitle("Scan Food")
            .sheet(isPresented: $showCamera) {
                CameraPicker(image: $image)
                    .onDisappear { Task { await analyze() } }
            }
        }
    }

    private func analyze() async {
        guard let image,
              let data = image.jpegData(compressionQuality: 0.8),
              let token = authManager.token else { return }
        do {
            analysis = try await APIClient.shared.uploadImage(path: "analyze-food-image", token: token, imageData: data)
        } catch {
            self.error = error.localizedDescription
        }
    }

    private func logMeal(from analysis: AnalyzeFoodImageResponse) async {
        guard let token = authManager.token else { return }
        let payload = FoodLogPayload(mealType: "meal", foods: analysis.foods, calories: analysis.caloriesEstimate, eatenAt: Date())
        UserDefaults.standard.set(Date(), forKey: "lastMealDate")
        do {
            try await APIClient.shared.requestNoResponse(path: "log-food", token: token, payload: payload)
        } catch {
            syncManager.enqueue(endpoint: "log-food", payload: payload)
        }
    }
}
