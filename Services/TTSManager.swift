import Foundation
import AVFoundation
import Combine

/// TTSManager — Unified TTS manager for iOS.
///
/// Manages both Piper and Coqui engines, with automatic failover
/// and a shared queue. Exposes a single `speak()` call to the app.
class TTSManager: ObservableObject {

    // MARK: - Published State
    @Published var activeEngine: String = "system"
    @Published var isSpeaking = false
    @Published var isConnected = false
    @Published var diagnostics: [DiagnosticEntry] = []

    struct DiagnosticEntry: Identifiable {
        let id = UUID()
        let timestamp: Date
        let level: Level
        let message: String
        enum Level: String { case info, warning, error }
    }

    // MARK: - Engines
    let coquiService: CoquiTTSService
    let piperService: PiperService
    private let systemSynth = AVSpeechSynthesizer()

    // MARK: - Queue
    private var queue: [(text: String, voice: String, speed: Float)] = []
    private var isProcessing = false
    private let lock = NSLock()
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Init

    init(serverHost: String = "127.0.0.1", serverPort: Int = 9000) {
        self.coquiService = CoquiTTSService(serverHost: serverHost, serverPort: serverPort)
        self.piperService = PiperService()

        // Observe Coqui readiness
        coquiService.$isReady
            .receive(on: DispatchQueue.main)
            .sink { [weak self] ready in
                self?.updateActiveEngine()
                self?.isConnected = ready
            }
            .store(in: &cancellables)

        coquiService.$currentEngine
            .receive(on: DispatchQueue.main)
            .sink { [weak self] engine in
                self?.activeEngine = engine.rawValue
                self?.log(.info, "TTS engine: \(engine.rawValue)")
            }
            .store(in: &cancellables)

        coquiService.$isSpeaking
            .receive(on: DispatchQueue.main)
            .sink { [weak self] speaking in
                self?.isSpeaking = speaking
            }
            .store(in: &cancellables)

        coquiService.$lastError
            .compactMap { $0 }
            .receive(on: DispatchQueue.main)
            .sink { [weak self] error in
                self?.log(.error, error)
            }
            .store(in: &cancellables)
    }

    // MARK: - Public API

    /// Speak text using the best available engine.
    func speak(_ text: String, voice: String = "en-default", speed: Float = 1.0) {
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }

        if coquiService.isReady {
            coquiService.speak(text, voice: voice, speed: speed)
        } else {
            // Fallback to system
            let utterance = AVSpeechUtterance(string: text)
            utterance.rate = speed * AVSpeechUtteranceDefaultSpeechRate
            utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
            systemSynth.speak(utterance)
        }
    }

    /// Stop all speech output.
    func stop() {
        coquiService.stop()
        systemSynth.stopSpeaking(at: .immediate)
    }

    /// Reconnect the WebSocket to the server.
    func reconnect() {
        log(.info, "Reconnecting to TTS server...")
        coquiService.connectWebSocket()
    }

    // MARK: - Internal

    private func updateActiveEngine() {
        if coquiService.isReady {
            activeEngine = coquiService.currentEngine.rawValue
        } else {
            activeEngine = "System (offline)"
        }
    }

    func log(_ level: DiagnosticEntry.Level, _ message: String) {
        let entry = DiagnosticEntry(timestamp: Date(), level: level, message: message)
        DispatchQueue.main.async {
            self.diagnostics.insert(entry, at: 0)
            if self.diagnostics.count > 200 { self.diagnostics = Array(self.diagnostics.prefix(200)) }
        }
    }
}
