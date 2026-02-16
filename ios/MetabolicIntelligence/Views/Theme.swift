import SwiftUI

extension Color {
    static let emerald = Color(red: 0.0, green: 0.84, blue: 0.62)
}

struct EmeraldButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundStyle(.black)
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color.emerald.opacity(configuration.isPressed ? 0.8 : 1.0), in: RoundedRectangle(cornerRadius: 12))
    }
}

struct CardStyle: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.white.opacity(0.06), in: RoundedRectangle(cornerRadius: 14))
    }
}
