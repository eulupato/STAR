import SwiftUI
import UIKit

struct ContentView: View {
    @EnvironmentObject private var state: AppState
    @State private var showCamera = false

    init() {
        UITextView.appearance().backgroundColor = .clear
    }

    var body: some View {
        ZStack {
            Color(hex: "#05030D")
                .ignoresSafeArea()
            Color(hex: state.theme["background"] ?? "#05030D")
                .ignoresSafeArea()
            RadialGradient(
                colors: [primary.opacity(0.22), Color.clear],
                center: .top, startRadius: 10, endRadius: 420
            )
            .ignoresSafeArea()

            ScrollView {
                VStack(spacing: 14) {
                    StarOrbView(state: state.currentState ?? "neutral", size: 160)
                        .padding(.top, 4)

                    Text("✦ \(state.label("title", fallback: "STAR"))")
                        .font(.system(size: 30, weight: .bold, design: .rounded))
                        .foregroundColor(textColor)

                    Text(state.status)
                        .font(.footnote.weight(.semibold))
                        .foregroundColor(accent)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 7)
                        .background(surface.opacity(0.9))
                        .overlay(Capsule().stroke(border, lineWidth: 1))
                        .clipShape(Capsule())

                    connectionCard
                    interactionCard

                    Text(state.response)
                        .font(.body)
                        .foregroundColor(textColor)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(14)
                        .background(surface)
                        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                        .textSelection(.enabled)

                    if !state.runtimeRevision.isEmpty {
                        Text("runtime \(state.runtimeRevision)")
                            .font(.caption2.monospaced())
                            .foregroundColor(muted)
                    }
                }
                .padding(18)
                .frame(maxWidth: 720)
                .frame(maxWidth: .infinity)
            }
        }
        .sheet(isPresented: $showCamera) {
            CameraPicker { image in
                showCamera = false
                state.uploadImage(image)
            } onCancel: {
                showCamera = false
            }
        }
        .onAppear {
            state.refreshRuntime()
        }
    }

    private var connectionCard: some View {
        VStack(spacing: 10) {
            TextField("http://192.168.1.10:8765", text: $state.serverURL)
                .keyboardType(.URL)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled(true)
                .padding(12)
                .foregroundColor(textColor)
                .background(Color.black.opacity(0.18))
                .clipShape(RoundedRectangle(cornerRadius: 12))

            SecureField("Código de pareamento", text: $state.pairingCode)
                .keyboardType(.numberPad)
                .padding(12)
                .foregroundColor(textColor)
                .background(Color.black.opacity(0.18))
                .clipShape(RoundedRectangle(cornerRadius: 12))

            actionButton(
                title: state.label("pair", fallback: "PAREAR"),
                emphasis: "primary",
                action: state.pair
            )
        }
        .padding(14)
        .background(surface)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(border, lineWidth: 1))
    }

    private var interactionCard: some View {
        VStack(spacing: 10) {
            TextEditor(text: $state.message)
                .frame(minHeight: 88, maxHeight: 130)
                .padding(6)
                .foregroundColor(textColor)
                .background(Color.black.opacity(0.18))
                .clipShape(RoundedRectangle(cornerRadius: 12))

            if state.feature("text", fallback: true) {
                actionButton(
                    title: "💬 " + state.label("send", fallback: "ENVIAR"),
                    emphasis: "accent",
                    action: state.sendText
                )
            }

            if state.feature("voice_input", fallback: true) {
                actionButton(
                    title: state.isRecording
                        ? "■ " + state.label("stop_and_send", fallback: "ENVIAR ÁUDIO")
                        : "🎙 " + state.label("speak", fallback: "FALAR"),
                    emphasis: "secondary",
                    action: state.toggleVoiceCommand
                )
            }

            if state.feature("camera_transport", fallback: true) {
                actionButton(
                    title: "📷 " + state.label("camera", fallback: "MOSTRAR À STAR"),
                    emphasis: "primary",
                    action: { showCamera = true }
                )
            }

            if state.feature("sensor_transport", fallback: true) {
                actionButton(
                    title: state.sensorsActive
                        ? "■ SENSORES ATIVOS"
                        : "🛰 " + state.label("sensors", fallback: "SENSORES"),
                    emphasis: "accent",
                    action: state.toggleSensors
                )

                actionButton(
                    title: "📏 " + state.label("measure", fallback: "MEDIR"),
                    emphasis: "secondary",
                    action: state.measurePhysical
                )
            }
        }
        .padding(14)
        .background(surface)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(border, lineWidth: 1))
    }

    /// Crystal-gradient button: primary → secondary tokens, with `emphasis` choosing which token leads.
    private func actionButton(
        title: String,
        emphasis: String = "primary",
        action: @escaping () -> Void
    ) -> some View {
        let lead = Color(hex: state.theme[emphasis] ?? "#7E58B3")
        return Button(action: action) {
            Text(title)
                .font(.system(size: 16, weight: .bold, design: .rounded))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .foregroundColor(textColor)
                .background(
                    LinearGradient(colors: [lead, primary, secondary], startPoint: .topLeading, endPoint: .bottomTrailing)
                )
                .overlay(
                    RoundedRectangle(cornerRadius: 13, style: .continuous)
                        .stroke(accent.opacity(0.55), lineWidth: 1)
                )
                .clipShape(RoundedRectangle(cornerRadius: 13, style: .continuous))
                .shadow(color: primary.opacity(0.45), radius: 8, x: 0, y: 2)
        }
        .buttonStyle(.plain)
    }

    private var surface: Color { Color(hex: state.theme["surface"] ?? "#160F2E") }
    private var border: Color { Color(hex: state.theme["border"] ?? "#3A2467") }
    private var primary: Color { Color(hex: state.theme["primary"] ?? "#7E58B3") }
    private var secondary: Color { Color(hex: state.theme["secondary"] ?? "#A192C6") }
    private var accent: Color { Color(hex: state.theme["accent"] ?? "#C49EE0") }
    private var textColor: Color { Color(hex: state.theme["text"] ?? "#F3EEFF") }
    private var muted: Color { Color(hex: state.theme["muted"] ?? "#A99CC9") }
}

private struct CameraPicker: UIViewControllerRepresentable {
    let onImage: (UIImage) -> Void
    let onCancel: () -> Void

    func makeCoordinator() -> Coordinator {
        Coordinator(onImage: onImage, onCancel: onCancel)
    }

    func makeUIViewController(context: Context) -> UIImagePickerController {
        let picker = UIImagePickerController()
        picker.delegate = context.coordinator
        picker.sourceType = UIImagePickerController.isSourceTypeAvailable(.camera) ? .camera : .photoLibrary
        return picker
    }

    func updateUIViewController(_ uiViewController: UIImagePickerController, context: Context) {}

    final class Coordinator: NSObject, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
        let onImage: (UIImage) -> Void
        let onCancel: () -> Void

        init(onImage: @escaping (UIImage) -> Void, onCancel: @escaping () -> Void) {
            self.onImage = onImage
            self.onCancel = onCancel
        }

        func imagePickerController(
            _ picker: UIImagePickerController,
            didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey: Any]
        ) {
            guard let image = info[.originalImage] as? UIImage else {
                onCancel()
                return
            }
            onImage(image)
        }

        func imagePickerControllerDidCancel(_ picker: UIImagePickerController) {
            onCancel()
        }
    }
}

private extension Color {
    init(hex: String) {
        let cleaned = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var value: UInt64 = 0
        Scanner(string: cleaned).scanHexInt64(&value)
        let r, g, b: UInt64
        if cleaned.count == 6 {
            r = (value >> 16) & 0xFF
            g = (value >> 8) & 0xFF
            b = value & 0xFF
        } else {
            r = 5
            g = 3
            b = 13
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: 1
        )
    }
}
