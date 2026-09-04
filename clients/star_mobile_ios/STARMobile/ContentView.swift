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
            Color(hex: state.theme["background"] ?? "#080B12")
                .ignoresSafeArea()

            ScrollView {
                VStack(spacing: 14) {
                    Text("⭐ \(state.label("title", fallback: "STAR"))")
                        .font(.system(size: 30, weight: .bold, design: .rounded))
                        .foregroundColor(Color(hex: state.theme["text"] ?? "#FFFFFF"))

                    Text(state.status)
                        .font(.footnote.weight(.semibold))
                        .foregroundColor(Color(hex: state.theme["accent"] ?? "#6CC8FF"))
                        .padding(.horizontal, 14)
                        .padding(.vertical, 7)
                        .background(surface.opacity(0.9))
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
                color: Color(hex: state.theme["primary"] ?? "#F6D35F"),
                foreground: .black,
                action: state.pair
            )
        }
        .padding(14)
        .background(surface)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
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
                    color: Color(hex: state.theme["accent"] ?? "#6CC8FF"),
                    foreground: .black,
                    action: state.sendText
                )
            }

            if state.feature("voice_input", fallback: true) {
                actionButton(
                    title: state.isRecording
                        ? "■ " + state.label("stop_and_send", fallback: "ENVIAR ÁUDIO")
                        : "🎙 " + state.label("speak", fallback: "FALAR"),
                    color: Color(hex: state.theme["secondary"] ?? "#F18ACB"),
                    foreground: .black,
                    action: state.toggleVoiceCommand
                )
            }

            if state.feature("camera_transport", fallback: true) {
                actionButton(
                    title: "📷 " + state.label("camera", fallback: "MOSTRAR À STAR"),
                    color: Color(hex: state.theme["primary"] ?? "#F6D35F"),
                    foreground: .black,
                    action: { showCamera = true }
                )
            }
        }
        .padding(14)
        .background(surface)
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
    }

    private func actionButton(
        title: String,
        color: Color,
        foreground: Color,
        action: @escaping () -> Void
    ) -> some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: 16, weight: .bold, design: .rounded))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .foregroundColor(foreground)
                .background(color)
                .clipShape(RoundedRectangle(cornerRadius: 13, style: .continuous))
        }
        .buttonStyle(.plain)
    }

    private var surface: Color {
        Color(hex: state.theme["surface"] ?? "#111827")
    }

    private var textColor: Color {
        Color(hex: state.theme["text"] ?? "#FFFFFF")
    }

    private var muted: Color {
        Color(hex: state.theme["muted"] ?? "#A8B0C0")
    }
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
            r = 8
            g = 11
            b = 18
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
