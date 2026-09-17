import ARKit
import CoreLocation
import CoreMotion
import Foundation
import HealthKit

/// Sensores reais do iPhone. Nada é iniciado até `start()` e tudo é interrompido
/// em `stop()`. Ausência de hardware/permissão gera ausência, nunca valor sintético.
final class DeviceSensorBridge: NSObject, CLLocationManagerDelegate, ARSessionDelegate {
    typealias BatchSink = ([[String: Any]]) -> Void
    typealias StatusSink = (String) -> Void

    private let location = CLLocationManager()
    private let motion = CMMotionManager()
    private let health = HKHealthStore()
    private let arSession = ARSession()
    private let queue = OperationQueue()
    private let lock = NSLock()
    private var latest: [String: [String: Any]] = [:]
    private var flushTimer: Timer?
    private var healthTimer: Timer?
    private var depthCompletion: ((Result<Double, Error>) -> Void)?
    private var depthRequestID = UUID()
    private let onBatch: BatchSink
    private let onStatus: StatusSink
    private(set) var active = false

    init(onBatch: @escaping BatchSink, onStatus: @escaping StatusSink) {
        self.onBatch = onBatch
        self.onStatus = onStatus
        super.init()
        location.delegate = self
        location.desiredAccuracy = kCLLocationAccuracyBest
        location.distanceFilter = 2
        arSession.delegate = self
        queue.name = "star-ios-sensors"
        queue.maxConcurrentOperationCount = 1
    }

    func start() {
        guard !active else { return }
        active = true
        location.requestWhenInUseAuthorization()
        startLocationIfAllowed()
        startMotion()
        startHealth()
        flushTimer?.invalidate()
        flushTimer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { [weak self] _ in self?.flush() }
        onStatus("Sensores reais ativos enquanto o app estiver aberto.")
    }

    func stop() {
        active = false
        location.stopUpdatingLocation()
        motion.stopAccelerometerUpdates()
        motion.stopGyroUpdates()
        motion.stopDeviceMotionUpdates()
        flushTimer?.invalidate(); flushTimer = nil
        healthTimer?.invalidate(); healthTimer = nil
        arSession.pause()
        if let completion = depthCompletion {
            depthCompletion = nil
            completion(.failure(SensorError("Medição interrompida.")))
        }
        lock.lock(); latest.removeAll(); lock.unlock()
        onStatus("Sensores pausados. Nenhuma coleta continua em background.")
    }

    private func timestamp() -> Double { Date().timeIntervalSince1970 * 1000 }

    private func put(_ kind: String, _ values: [String: Any]) {
        guard active else { return }
        var sample = values
        sample["kind"] = kind
        if sample["timestamp"] == nil {
            sample["timestamp"] = timestamp()
        }
        lock.lock(); latest[kind] = sample; lock.unlock()
    }

    private func flush() {
        guard active else { return }
        lock.lock(); let values = Array(latest.values); latest.removeAll(); lock.unlock()
        if !values.isEmpty { onBatch(values) }
    }

    private func emitImmediate(_ kind: String, _ values: [String: Any]) {
        var sample = values
        sample["kind"] = kind
        if sample["timestamp"] == nil {
            sample["timestamp"] = timestamp()
        }
        onBatch([sample])
    }

    private func startLocationIfAllowed() {
        let status = location.authorizationStatus
        if status == .authorizedWhenInUse || status == .authorizedAlways { location.startUpdatingLocation() }
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        if active { startLocationIfAllowed() }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let value = locations.last else { return }
        put("location", [
            "latitude": value.coordinate.latitude,
            "longitude": value.coordinate.longitude,
            "accuracy_m": max(0, value.horizontalAccuracy),
            "timestamp": value.timestamp.timeIntervalSince1970 * 1000
        ])
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        onStatus("GPS indisponível: \(error.localizedDescription)")
    }

    private func startMotion() {
        if motion.isAccelerometerAvailable {
            motion.accelerometerUpdateInterval = 0.2
            motion.startAccelerometerUpdates(to: queue) { [weak self] data, _ in
                guard let self, let a = data?.acceleration else { return }
                let g = 9.80665
                self.put("accelerometer", ["x": a.x * g, "y": a.y * g, "z": a.z * g, "unit": "m/s^2"])
            }
        }
        if motion.isGyroAvailable {
            motion.gyroUpdateInterval = 0.2
            motion.startGyroUpdates(to: queue) { [weak self] data, _ in
                guard let self, let r = data?.rotationRate else { return }
                self.put("gyroscope", ["x": r.x, "y": r.y, "z": r.z, "unit": "rad/s"])
            }
        }
        if motion.isDeviceMotionAvailable {
            motion.deviceMotionUpdateInterval = 0.2
            motion.startDeviceMotionUpdates(to: queue) { [weak self] data, _ in
                guard let self, let q = data?.attitude.quaternion else { return }
                self.put("rotation_vector", ["x": q.x, "y": q.y, "z": q.z, "unit": "quaternion-vector"])
            }
        }
    }

    private func startHealth() {
        guard HKHealthStore.isHealthDataAvailable(),
              let heart = HKObjectType.quantityType(forIdentifier: .heartRate) else { return }
        health.requestAuthorization(toShare: [], read: [heart]) { [weak self] success, _ in
            guard let self, success, self.active else { return }
            DispatchQueue.main.async {
                self.queryHeartRate()
                self.healthTimer?.invalidate()
                self.healthTimer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in self?.queryHeartRate() }
            }
        }
    }

    private func queryHeartRate() {
        guard active, let heart = HKObjectType.quantityType(forIdentifier: .heartRate) else { return }
        let sort = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)
        let query = HKSampleQuery(sampleType: heart, predicate: nil, limit: 1, sortDescriptors: [sort]) { [weak self] _, samples, _ in
            guard let self, let sample = samples?.first as? HKQuantitySample else { return }
            let bpm = sample.quantity.doubleValue(for: HKUnit.count().unitDivided(by: .minute()))
            if bpm > 0 {
                self.put("heart_rate", [
                    "bpm": bpm,
                    "accuracy": "healthkit-sample",
                    "timestamp": sample.endDate.timeIntervalSince1970 * 1000
                ])
            }
        }
        health.execute(query)
    }

    /// Mede profundidade central somente em hardware com ARKit sceneDepth (LiDAR/ToF).
    func measureDepth(completion: @escaping (Result<Double, Error>) -> Void) {
        guard depthCompletion == nil else {
            completion(.failure(SensorError("Já existe uma medição física em andamento."))); return
        }
        guard ARWorldTrackingConfiguration.isSupported else {
            completion(.failure(SensorError("ARKit não suportado neste aparelho."))); return
        }
        let configuration = ARWorldTrackingConfiguration()
        guard ARWorldTrackingConfiguration.supportsFrameSemantics(.sceneDepth) else {
            completion(.failure(SensorError("Este aparelho não oferece sceneDepth/LiDAR."))); return
        }
        configuration.frameSemantics.insert(.sceneDepth)
        let requestID = UUID()
        depthRequestID = requestID
        depthCompletion = completion
        arSession.run(configuration, options: [.resetTracking])
        DispatchQueue.main.asyncAfter(deadline: .now() + 5) { [weak self] in
            guard let self, self.depthRequestID == requestID, let pending = self.depthCompletion else { return }
            self.depthCompletion = nil
            self.arSession.pause()
            pending(.failure(SensorError("O sensor de profundidade não entregou uma leitura válida a tempo.")))
        }
    }

    func session(_ session: ARSession, didUpdate frame: ARFrame) {
        guard let completion = depthCompletion, let depth = frame.sceneDepth else { return }
        let buffer = depth.depthMap
        CVPixelBufferLockBaseAddress(buffer, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(buffer, .readOnly) }
        guard CVPixelBufferGetPixelFormatType(buffer) == kCVPixelFormatType_DepthFloat32,
              let base = CVPixelBufferGetBaseAddress(buffer) else { return }
        let width = CVPixelBufferGetWidth(buffer), height = CVPixelBufferGetHeight(buffer)
        let rowBytes = CVPixelBufferGetBytesPerRow(buffer)
        let y = height / 2, x = width / 2
        let row = base.advanced(by: y * rowBytes).assumingMemoryBound(to: Float32.self)
        let meters = Double(row[x])
        guard meters.isFinite, meters > 0 else { return }
        depthCompletion = nil
        arSession.pause()
        emitImmediate("lidar_depth", ["meters": meters, "method": "ios-arkit-sceneDepth"])
        completion(.success(meters))
    }

    func session(_ session: ARSession, didFailWithError error: Error) {
        guard let completion = depthCompletion else { return }
        depthCompletion = nil
        session.pause()
        completion(.failure(SensorError("ARKit: \(error.localizedDescription)")))
    }

    func sessionWasInterrupted(_ session: ARSession) {
        guard let completion = depthCompletion else { return }
        depthCompletion = nil
        session.pause()
        completion(.failure(SensorError("A sessão de profundidade foi interrompida.")))
    }
}

private struct SensorError: LocalizedError {
    let value: String
    init(_ value: String) { self.value = value }
    var errorDescription: String? { value }
}
