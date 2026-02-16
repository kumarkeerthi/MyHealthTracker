import SwiftUI

struct StrengthView: View {
    @State private var snapshot = StrengthSnapshot(
        strengthIndex: 78,
        gripStrengthKg: 49,
        pullUps: 14,
        deadHangSeconds: 95,
        pushUps: 42
    )

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 14) {
                    strengthIndexCard
                    countersCard
                    weeklyChartCard
                }
                .padding()
            }
            .background(Color.black.ignoresSafeArea())
            .navigationTitle("Strength")
        }
    }

    private var strengthIndexCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Strength Index")
                .font(.headline)
            Gauge(value: snapshot.strengthIndex, in: 0...100) {
                EmptyView()
            } currentValueLabel: {
                Text("\(Int(snapshot.strengthIndex))")
                    .font(.title2.bold())
            }
            .gaugeStyle(.accessoryCircular)
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text("Grip strength")
                    Spacer()
                    Text("\(Int((snapshot.gripStrengthKg / 70) * 100))%")
                }
                ProgressView(value: snapshot.gripStrengthKg / 70)
                    .tint(.emerald)
            }
        }
        .modifier(CardStyle())
    }

    private var countersCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Performance trackers")
                .font(.headline)
            counterRow("Pull-up count", value: "\(snapshot.pullUps)")
            counterRow("Dead hang timer", value: "\(snapshot.deadHangSeconds)s")
            counterRow("Pushup count", value: "\(snapshot.pushUps)")
        }
        .modifier(CardStyle())
    }

    private var weeklyChartCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Weekly strength chart")
                .font(.headline)
            HStack(alignment: .bottom, spacing: 8) {
                ForEach([62, 66, 69, 71, 74, 76, 78], id: \.self) { value in
                    RoundedRectangle(cornerRadius: 6)
                        .fill(Color.emerald.opacity(0.75))
                        .frame(height: CGFloat(value) * 1.2)
                }
            }
            .frame(height: 120, alignment: .bottom)
        }
        .modifier(CardStyle())
    }

    private func counterRow(_ title: String, value: String) -> some View {
        HStack {
            Text(title).foregroundStyle(.secondary)
            Spacer()
            Text(value).fontWeight(.semibold)
        }
    }
}
