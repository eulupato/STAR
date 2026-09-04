import AVFoundation
import Foundation
import UIKit

final class AppState: NSObject, ObservableObject {
    @Published var serverURL: String
    @Published var pairingCode = ""
    @Published var message = ""
    @Published var status = "● DESCONECTADO"
    @Published var response = "Resposta da STAR aparecerá aqui."
    @Published var isRecording = false
    @Published var runtimeRevision = ""
    @Published var labels: [String: String] = [
        "title": "STAR",
        "pair": "PAREAR",
        "send": "ENVIAR",
        "speak": "FALAR",
        "stop_and_send": "ENVIAR ÁUDIO",
        "camera": "MOSTRAR À STAR"
    ]
    @Published var theme: [String: String] = [
        "background": "#080B12",
        "surface": "#111827",
        "primary": "#F6D35F",
        "secondary": "#F18ACB",
        "accent": "#6CC8FF",
        "text": "#FFFFFF",
        "muted": "#A8B0C0"
    ]
    @Published var features: [String: Bool] = [
        "text": true,
        "voice_input": true,
        "spoken_reply": true,
        "camera_transport": true,
        "vision_analysis": false,
        "remote_pc_actions": false
    ]

    private let defaults = UserDefaults.standard
    private let speaker = AVSpeechSynthesizer()
    private var recorder: AVAudioRecorder?
    private var audioURL: URL?
    private var syncTimer: Timer?
    private var syncInterval: TimeInterval = 30

    override init() {
        serverURL = UserDefaults.standard.string(forKey: "star.server") ?? ""
        super.init()
        _ = deviceID
        if !token.isEmpty && !serverURL.isEmpty {
            status = "● PAREADO"
            startSyncLoop()
            refreshRuntime()
        }
    }

    deinit {
        syncTimer?.invalidate()
    }

    var token: String {
        defaults.string(forKey: "star.token") ?? ""
    }

    var deviceID: String {
        if let existing = defaults.string(forKey: "star.device_id"), !existing.isEmpty {
            return existing
        }
        let created = "iphone-" + UUID().uuidString.lowercased()
        defaults.set(created, forKey: "star.device_id")
        return created
    }

    var isPaired: Bool {
        !token.isEmpty
    }

    func label(_ key: String, fallback: String) -> String {
        labels[key] ?? fallback
    }

    func feature(_ key: String, fallback: Bool = false) -> Bool {
        features[key] ?? fallback
    }

    func pair() {
        let base = normalizedServer()
        guard base.hasPrefix("http://") || base.hasPrefix("https://") else {
            response = "Informe o endereço exibido pelo PC, incluindo http:// e a porta."
            return
        }
        guard pairingCode.count == 6 else {
            response = "Informe o código de pareamento de 6 dígitos exibido pelo PC."
            return
        }

        status = "● PAREANDO..."
        let bounds = UIScreen.main.nativeBounds
        let payload: [String: Any] = [
            "pairing_code": pairingCode,
            "device_id": deviceID,
            "name": "STAR Mobile iOS",
            "capabilities": ["microphone", "camera", "display", "speaker"],
            "metadata": [
                "platform": "ios",
                "form_factor": "phone",
                "os_version": UIDevice.current.systemVersion,
                "app_version": Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "0.1.0",
                "screen_width": Int(bounds.width),
                "screen_height": Int(bounds.height)
            ]
        ]

        request(path: "/v1/pair", method: "POST", json: payload, authenticated: false) { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let json):
                    guard let newToken = json["token"] as? String, !newToken.isEmpty else {
                        self.showError("O Core não devolveu token de pareamento.")
                        return
                    }
                    self.defaults.set(base, forKey: "star.server")
                    self.defaults.set(newToken, forKey: "star.token")
                    self.serverURL = base
                    self.pairingCode = ""
                    self.status = "● ONLINE"
                    self.response = "STAR Mobile pareado com o Core."
                    if let runtime = json["runtime"] as? [String: Any] {
                        self.applyRuntime(runtime)
                    }
                    self.startSyncLoop()
                case .failure(let error):
                    self.showError(error.localizedDescription)
                }
            }
        }
    }

    func sendText() {
        let text = message.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        guard isPaired else {
            response = "Pareie o iPhone com a STAR primeiro."
            return
        }

        status = "● STAR PENSANDO NO PC..."
        request(path: "/v1/text", method: "POST", json: ["text": text], authenticated: true) { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let json):
                    let answer = json["response"] as? String ?? "Sem resposta."
                    self.status = "● ONLINE"
                    self.response = answer
                    self.message = ""
                    self.speakIfEnabled(answer)
                case .failure(let error):
                    self.showError(error.localizedDescription)
                }
            }
        }
    }

    func toggleVoiceCommand() {
        if isRecording {
            stopRecordingAndSend()
            return
        }
        guard isPaired else {
            response = "Pareie o iPhone com a STAR primeiro."
            return
        }
        AVAudioSession.sharedInstance().requestRecordPermission { allowed in
            DispatchQueue.main.async {
                if allowed {
                    self.startRecording()
                } else {
                    self.response = "Permissão de microfone negada."
                }
            }
        }
    }

    private func startRecording() {
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(.playAndRecord, mode: .spokenAudio, options: [.defaultToSpeaker, .allowBluetooth])
            try session.setActive(true)

            let url = FileManager.default.temporaryDirectory.appendingPathComponent("star_mobile_audio.m4a")
            let settings: [String: Any] = [
                AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
                AVSampleRateKey: 44_100,
                AVNumberOfChannelsKey: 1,
                AVEncoderBitRateKey: 96_000
            ]
            recorder = try AVAudioRecorder(url: url, settings: settings)
            guard recorder?.record() == true else {
                throw STARClientError("Não foi possível iniciar a gravação.")
            }
            audioURL = url
            isRecording = true
            status = "● OUVINDO..."
        } catch {
            recorder = nil
            audioURL = nil
            isRecording = false
            showError("Microfone: \(error.localizedDescription)")
        }
    }

    private func stopRecordingAndSend() {
        recorder?.stop()
        recorder = nil
        isRecording = false
        status = "● TRANSCRIBINDO NO PC..."

        guard let url = audioURL else {
            showError("Arquivo de áudio ausente.")
            return
        }
        audioURL = nil

        do {
            let data = try Data(contentsOf: url)
            upload(path: "/v1/audio", data: data, contentType: "audio/mp4") { result in
                DispatchQueue.main.async {
                    switch result {
                    case .success(let json):
                        let transcript = json["transcript"] as? String ?? ""
                        let answer = json["response"] as? String ?? "Sem resposta."
                        self.status = "● ONLINE"
                        self.response = "Você: \(transcript)\n\nSTAR: \(answer)"
                        self.speakIfEnabled(answer)
                    case .failure(let error):
                        self.showError(error.localizedDescription)
                    }
                }
            }
        } catch {
            showError("Áudio: \(error.localizedDescription)")
        }
    }

    func uploadImage(_ image: UIImage) {
        guard isPaired else {
            response = "Pareie o iPhone com a STAR primeiro."
            return
        }
        guard let data = image.jpegData(compressionQuality: 0.88) else {
            showError("Não consegui converter a imagem para JPEG.")
            return
        }
        status = "● ENVIANDO IMAGEM..."
        upload(path: "/v1/image", data: data, contentType: "image/jpeg") { result in
            DispatchQueue.main.async {
                switch result {
                case .success(let json):
                    self.status = "● ONLINE"
                    self.response = json["message"] as? String ?? "Imagem recebida pelo Core."
                case .failure(let error):
                    self.showError(error.localizedDescription)
                }
            }
        }
    }

    func refreshRuntime() {
        guard isPaired, !normalizedServer().isEmpty else { return }
        request(path: "/v1/runtime", method: "GET", json: nil, authenticated: true) { result in
            DispatchQueue.main.async {
                if case .success(let json) = result {
                    self.applyRuntime(json)
                    self.status = "● ONLINE"
                }
            }
        }
    }

    private func heartbeat() {
        guard isPaired, !normalizedServer().isEmpty else { return }
        request(path: "/v1/heartbeat", method: "POST", json: [:], authenticated: true) { result in
            switch result {
            case .success(let json):
                if (json["runtime_changed"] as? Bool) == true {
                    self.refreshRuntime()
                } else {
                    DispatchQueue.main.async { self.status = "● ONLINE" }
                }
            case .failure:
                DispatchQueue.main.async { self.status = "● SEM CONEXÃO" }
            }
        }
    }

    private func startSyncLoop() {
        syncTimer?.invalidate()
        guard isPaired else { return }
        syncTimer = Timer.scheduledTimer(withTimeInterval: syncInterval, repeats: true) { [weak self] _ in
            self?.heartbeat()
        }
    }

    private func applyRuntime(_ runtime: [String: Any]) {
        let oldInterval = syncInterval
        if let revision = runtime["revision"] as? String {
            runtimeRevision = revision
        }
        if let rawLabels = runtime["labels"] as? [String: Any] {
            labels.merge(rawLabels.compactMapValues { $0 as? String }) { _, new in new }
        }
        if let rawTheme = runtime["theme"] as? [String: Any] {
            theme.merge(rawTheme.compactMapValues { $0 as? String }) { _, new in new }
        }
        if let rawFeatures = runtime["features"] as? [String: Any] {
            features.merge(rawFeatures.compactMapValues { $0 as? Bool }) { _, new in new }
        }
        if let interval = runtime["sync_interval_seconds"] as? NSNumber {
            syncInterval = max(10, interval.doubleValue)
        }
        if oldInterval != syncInterval, isPaired {
            startSyncLoop()
        }
    }

    private func speakIfEnabled(_ text: String) {
        guard feature("spoken_reply", fallback: true), !text.isEmpty else { return }
        speaker.stopSpeaking(at: .immediate)
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "pt-BR")
        utterance.rate = 0.48
        speaker.speak(utterance)
    }

    private func normalizedServer() -> String {
        var value = serverURL.trimmingCharacters(in: .whitespacesAndNewlines)
        while value.hasSuffix("/") { value.removeLast() }
        return value
    }

    private func request(
        path: String,
        method: String,
        json: [String: Any]?,
        authenticated: Bool,
        completion: @escaping (Result<[String: Any], Error>) -> Void
    ) {
        let base = normalizedServer()
        guard let url = URL(string: base + path) else {
            completion(.failure(STARClientError("Endereço do Core inválido.")))
            return
        }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.timeoutInterval = 120
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        if let json {
            do {
                request.httpBody = try JSONSerialization.data(withJSONObject: json)
                request.setValue("application/json; charset=utf-8", forHTTPHeaderField: "Content-Type")
            } catch {
                completion(.failure(error))
                return
            }
        }
        applyAuth(to: &request, authenticated: authenticated)
        perform(request, completion: completion)
    }

    private func upload(
        path: String,
        data: Data,
        contentType: String,
        completion: @escaping (Result<[String: Any], Error>) -> Void
    ) {
        let base = normalizedServer()
        guard let url = URL(string: base + path) else {
            completion(.failure(STARClientError("Endereço do Core inválido.")))
            return
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 120
        request.httpBody = data
        request.setValue(contentType, forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        applyAuth(to: &request, authenticated: true)
        perform(request, completion: completion)
    }

    private func applyAuth(to request: inout URLRequest, authenticated: Bool) {
        guard authenticated else { return }
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue(deviceID, forHTTPHeaderField: "X-STAR-Device")
        if !runtimeRevision.isEmpty {
            request.setValue(runtimeRevision, forHTTPHeaderField: "X-STAR-Runtime")
        }
    }

    private func perform(
        _ request: URLRequest,
        completion: @escaping (Result<[String: Any], Error>) -> Void
    ) {
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error {
                completion(.failure(error))
                return
            }
            guard let http = response as? HTTPURLResponse else {
                completion(.failure(STARClientError("Resposta HTTP inválida.")))
                return
            }
            let body = data ?? Data()
            let object: [String: Any]
            if body.isEmpty {
                object = [:]
            } else {
                do {
                    object = try JSONSerialization.jsonObject(with: body) as? [String: Any] ?? [:]
                } catch {
                    completion(.failure(error))
                    return
                }
            }
            guard (200..<300).contains(http.statusCode) else {
                let detail = object["detail"] as? String ?? object["error"] as? String ?? "HTTP \(http.statusCode)"
                completion(.failure(STARClientError(detail)))
                return
            }
            completion(.success(object))
        }.resume()
    }

    private func showError(_ message: String) {
        status = "● ERRO"
        response = message
    }
}

private struct STARClientError: LocalizedError {
    let message: String

    init(_ message: String) {
        self.message = message
    }

    var errorDescription: String? { message }
}
