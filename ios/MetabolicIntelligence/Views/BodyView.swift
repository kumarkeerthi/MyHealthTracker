import SwiftUI

struct BodyView: View {
    @EnvironmentObject private var healthKitManager: HealthKitManager
    @State private var weekMode = false

    private var insulinScore: Double {
        healthKitManager.latestSnapshot?.postMealWalkBonus == true ? 34 : 52
    }

    private var hydrationMet: Bool {
        (healthKitManager.latestSnapshot?.sleepHours ?? 0) >= 7
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 16) {
                    Toggle("Weekly comparison mode", isOn: $weekMode)
                        .tint(.emerald)
                        .modifier(CardStyle())

                    silhouetteCard
                    comparisonCard
                }
                .padding()
            }
            .background(Color.black.ignoresSafeArea())
            .navigationTitle("Body")
        }
    }

    private var silhouetteCard: some View {
        VStack(spacing: 14) {
            ZStack {
                Capsule()
                    .fill(Color.white.opacity(0.08))
                    .frame(width: 150, height: 320)
                    .overlay(alignment: .center) {
                        RoundedRectangle(cornerRadius: 18)
                            .fill(Color.emerald.opacity(insulinScore < 40 ? 0.30 : 0.12))
                            .frame(width: weekMode ? 58 : 72, height: 110)
                            .blur(radius: insulinScore < 40 ? 8 : 2)
                            .offset(y: 24)
                            .animation(.easeInOut(duration: 0.5), value: weekMode)
                    }
                    .overlay(alignment: .bottom) {
                        if hydrationMet {
                            Circle()
                                .fill(LinearGradient(colors: [.emerald.opacity(0.45), .clear], startPoint: .top, endPoint: .bottom))
                                .frame(width: 180, height: 120)
                                .offset(y: 26)
                        }
                    }

                Circle()
                    .stroke(Color.emerald.opacity(0.3), lineWidth: 2)
                    .frame(width: 220, height: 220)
                    .blur(radius: 8)
            }

            Text("Waist narrowing and abdomen glow react to insulin load and hydration/protein readiness.")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
        .modifier(CardStyle())
    }

    private var comparisonCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Weekly body comparison")
                .font(.headline)
            HStack(alignment: .bottom, spacing: 16) {
                comparisonBar(label: "Week -1", value: weekMode ? 0.58 : 0.62)
                comparisonBar(label: "This week", value: weekMode ? 0.51 : 0.55)
            }
        }
        .modifier(CardStyle())
    }

    private func comparisonBar(label: String, value: Double) -> some View {
        VStack(spacing: 8) {
            RoundedRectangle(cornerRadius: 8)
                .fill(Color.emerald.opacity(0.7))
                .frame(width: 72, height: 180 * value)
            Text(label)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
}
