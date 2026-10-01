import SwiftUI

/// Animated "Cosmic Crystal" orb: N luminous great circles projected in perspective.
/// Mirrors gui/visual3d.py (orb_filaments + project) and gui/theme.py (STATE_COLORS / STATE_MOTION).
/// iOS 15+, no external dependencies: TimelineView drives a Canvas at ~30 fps.
struct StarOrbView: View {
    var state: String = "neutral"
    var size: CGFloat = 180

    private static let filamentCount = 7
    private static let samplesPerFilament = 56
    private static let fov: Double = 300
    private static let cameraDistance: Double = 3.2
    private static let background = OrbRGB(hex: "#05030D")
    private static let orbCore = OrbRGB(hex: "#57388F")

    private struct Palette { let primary: OrbRGB; let secondary: OrbRGB; let glow: OrbRGB }
    private struct Motion { let speed: Double; let pulse: Double; let wobble: Double }

    private var palette: Palette {
        switch state {
        case "listening": return Palette(primary: OrbRGB(hex: "#638CBF"), secondary: OrbRGB(hex: "#555F9F"), glow: OrbRGB(hex: "#B5AFD3"))
        case "thinking": return Palette(primary: OrbRGB(hex: "#A192C6"), secondary: OrbRGB(hex: "#7E58B3"), glow: OrbRGB(hex: "#C49EE0"))
        case "speaking": return Palette(primary: OrbRGB(hex: "#E6B8E0"), secondary: OrbRGB(hex: "#A192C6"), glow: OrbRGB(hex: "#E6DCEA"))
        case "error": return Palette(primary: OrbRGB(hex: "#FF7C87"), secondary: OrbRGB(hex: "#7E58B3"), glow: OrbRGB(hex: "#FFD36E"))
        default: return Palette(primary: OrbRGB(hex: "#7E58B3"), secondary: OrbRGB(hex: "#3A2467"), glow: OrbRGB(hex: "#C49EE0"))
        }
    }

    private var motion: Motion {
        switch state {
        case "listening": return Motion(speed: 0.55, pulse: 0.06, wobble: 0.07)
        case "thinking": return Motion(speed: 0.95, pulse: 0.04, wobble: 0.10)
        case "speaking": return Motion(speed: 0.70, pulse: 0.09, wobble: 0.08)
        case "error": return Motion(speed: 0.25, pulse: 0.02, wobble: 0.02)
        default: return Motion(speed: 0.35, pulse: 0.03, wobble: 0.04)
        }
    }

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30.0)) { timeline in
            Canvas { context, canvasSize in
                draw(in: &context, size: canvasSize, time: timeline.date.timeIntervalSinceReferenceDate)
            }
        }
        .frame(width: size, height: size)
        .animation(.easeInOut(duration: 0.5), value: state)
        .accessibilityLabel(Text("Orbe da STAR: \(state)"))
    }

    private func draw(in context: inout GraphicsContext, size canvasSize: CGSize, time: Double) {
        let pal = palette
        let mot = motion
        let cx = Double(canvasSize.width) / 2
        let cy = Double(canvasSize.height) / 2
        let pulse = 1 + mot.pulse * sin(time * 2.4)
        let radius = Double(min(canvasSize.width, canvasSize.height)) * 0.36 * pulse
        // Perspective scale so the sphere (unit radius) fills `radius` pixels at z = 0.
        let worldScale = radius * Self.cameraDistance / Self.fov

        // Halo + inner nebula
        let halo = Path(ellipseIn: CGRect(x: cx - radius * 1.45, y: cy - radius * 1.45, width: radius * 2.9, height: radius * 2.9))
        context.fill(halo, with: .radialGradient(
            Gradient(colors: [pal.glow.color(0.22), pal.primary.color(0.10), Self.background.color(0)]),
            center: CGPoint(x: cx, y: cy), startRadius: radius * 0.2, endRadius: radius * 1.45))
        let core = Path(ellipseIn: CGRect(x: cx - radius, y: cy - radius, width: radius * 2, height: radius * 2))
        context.fill(core, with: .radialGradient(
            Gradient(colors: [pal.secondary.color(0.45), Self.orbCore.color(0.18), Self.background.color(0.0)]),
            center: CGPoint(x: cx - radius * 0.15, y: cy + radius * 0.1), startRadius: 0, endRadius: radius))

        let spin = time * mot.speed
        var segments: [(z: Double, a: CGPoint, b: CGPoint)] = []
        segments.reserveCapacity(Self.filamentCount * Self.samplesPerFilament)

        for i in 0..<Self.filamentCount {
            let fi = Double(i)
            let tilt = 0.35 + fi * (Double.pi / Double(Self.filamentCount)) + mot.wobble * sin(time * 0.9 + fi)
            let yaw = spin * (1 + 0.18 * fi) + fi * 0.9
            let roll = 0.25 * sin(spin * 0.6 + fi * 1.7)
            var previous: (x: Double, y: Double, z: Double)?
            for s in 0...Self.samplesPerFilament {
                let t = Double(s) / Double(Self.samplesPerFilament) * 2 * Double.pi
                var p = (x: cos(t), y: sin(t), z: 0.0)
                p = rotateX(p, tilt)
                p = rotateY(p, yaw)
                p = rotateZ(p, roll)
                if let prev = previous {
                    let a = project(prev, cx: cx, cy: cy, scale: worldScale)
                    let b = project(p, cx: cx, cy: cy, scale: worldScale)
                    segments.append((z: (prev.z + p.z) / 2, a: a, b: b))
                }
                previous = p
            }
        }

        // Painter's algorithm: far segments first so near filaments glow on top.
        segments.sort { $0.z < $1.z }
        for seg in segments {
            let depth = (seg.z + 1) / 2 // 0 = back, 1 = front
            let color = Self.orbCore.mix(pal.glow, depth)
            var path = Path()
            path.move(to: seg.a)
            path.addLine(to: seg.b)
            let width = 0.6 + 2.2 * depth
            context.stroke(path, with: .color(pal.primary.color(0.10 + 0.18 * depth)),
                           style: StrokeStyle(lineWidth: width * 3, lineCap: .round))
            context.stroke(path, with: .color(color.color(0.25 + 0.75 * depth)),
                           style: StrokeStyle(lineWidth: width, lineCap: .round))
        }
    }

    private func project(_ p: (x: Double, y: Double, z: Double), cx: Double, cy: Double, scale: Double) -> CGPoint {
        let factor = Self.fov / (Self.cameraDistance - p.z)
        return CGPoint(x: cx + p.x * factor * scale, y: cy - p.y * factor * scale)
    }

    private func rotateX(_ p: (x: Double, y: Double, z: Double), _ a: Double) -> (x: Double, y: Double, z: Double) {
        (p.x, p.y * cos(a) - p.z * sin(a), p.y * sin(a) + p.z * cos(a))
    }

    private func rotateY(_ p: (x: Double, y: Double, z: Double), _ a: Double) -> (x: Double, y: Double, z: Double) {
        (p.x * cos(a) + p.z * sin(a), p.y, -p.x * sin(a) + p.z * cos(a))
    }

    private func rotateZ(_ p: (x: Double, y: Double, z: Double), _ a: Double) -> (x: Double, y: Double, z: Double) {
        (p.x * cos(a) - p.y * sin(a), p.x * sin(a) + p.y * cos(a), p.z)
    }
}

/// Minimal RGB helper (kept local so StarOrbView has no dependency on other files).
struct OrbRGB {
    let r: Double
    let g: Double
    let b: Double

    init(r: Double, g: Double, b: Double) { self.r = r; self.g = g; self.b = b }

    init(hex: String) {
        let cleaned = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var value: UInt64 = 0
        Scanner(string: cleaned).scanHexInt64(&value)
        if cleaned.count == 6 {
            r = Double((value >> 16) & 0xFF) / 255
            g = Double((value >> 8) & 0xFF) / 255
            b = Double(value & 0xFF) / 255
        } else {
            r = 5.0 / 255; g = 3.0 / 255; b = 13.0 / 255
        }
    }

    func mix(_ other: OrbRGB, _ t: Double) -> OrbRGB {
        let k = max(0, min(1, t))
        return OrbRGB(r: r + (other.r - r) * k, g: g + (other.g - g) * k, b: b + (other.b - b) * k)
    }

    func color(_ opacity: Double = 1) -> Color {
        Color(.sRGB, red: r, green: g, blue: b, opacity: opacity)
    }
}

#if DEBUG
struct StarOrbView_Previews: PreviewProvider {
    static var previews: some View {
        ZStack {
            Color(.sRGB, red: 5.0 / 255, green: 3.0 / 255, blue: 13.0 / 255, opacity: 1).ignoresSafeArea()
            StarOrbView(state: "thinking", size: 220)
        }
    }
}
#endif
