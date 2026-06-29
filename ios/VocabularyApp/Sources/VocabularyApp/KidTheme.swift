import SwiftUI

/// Kid-friendly palette, fonts, and button styles.
public enum KidTheme {
    public static let purple = Color(red: 0.45, green: 0.35, blue: 0.95)
    public static let pink = Color(red: 0.98, green: 0.40, blue: 0.65)
    public static let green = Color(red: 0.25, green: 0.78, blue: 0.45)
    public static let orange = Color(red: 1.00, green: 0.60, blue: 0.20)
    public static let blue = Color(red: 0.25, green: 0.62, blue: 0.98)
    public static let yellow = Color(red: 1.00, green: 0.82, blue: 0.25)

    public static func gradeColor(_ level: Int) -> Color {
        switch level {
        case 1: return pink
        case 2: return orange
        case 3: return yellow
        case 4: return green
        case 5: return blue
        case 6: return purple
        default: return purple
        }
    }

    public static func title(_ s: String) -> Text {
        Text(s).font(.system(.largeTitle, design: .rounded).weight(.heavy))
    }
}

/// Big, bouncy primary button for small hands.
public struct BigButtonStyle: ButtonStyle {
    let color: Color
    public init(color: Color = KidTheme.purple) { self.color = color }
    public func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(.title3, design: .rounded).weight(.bold))
            .frame(maxWidth: .infinity)
            .padding(.vertical, 18)
            .background(color, in: RoundedRectangle(cornerRadius: 22))
            .foregroundStyle(.white)
            .shadow(color: color.opacity(0.4), radius: 8, y: 4)
            .scaleEffect(configuration.isPressed ? 0.96 : 1)
            .animation(.spring(response: 0.3, dampingFraction: 0.6), value: configuration.isPressed)
    }
}
