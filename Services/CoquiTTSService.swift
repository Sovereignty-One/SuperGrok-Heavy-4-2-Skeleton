import Foundation
import AVFoundation
import Combine

/// CoquiTTSService — Real Coqui/XTTS voice synthesis for iOS.
///
/// Connects to the SuperGrok Unified Server WebSocket for server-side
/// Coqui TTS synthesis, with on-device AVSpeechSynthesizer fallback.
/// Supports queued requests, multiple voices, and speed control.
class CoquiTTSService: ObservableObject {

    // MARK: - Published State
    @Published var isReady = false
    @Published var isSpeaking = false
    @Published var currentEngine: TTSEngine = .coqui
    @Published var lastError: String?

    enum TTSEngine: String, CaseIterable {
        case coqui   = "Coqui XTTS"
        case piper   = "Piper"
        case system  = "System"
    }

    // MARK: - Audio Playback
    private let audioEngine = AVAudioEngine()
    private let playerNode = AVAudioPlayerNode()

    // MARK: - Queue
    private var ttsQueue: [(text: String, voice: String, speed: Float)] = []
    private var isProcessing = false
    private let queueLock = NSLock()

    // MARK: - WebSocket
    private var webSocket: URLSessionWebSocketTask?
    private let serverURL: URL
    private var session: URLSession

    // MARK: - Fallback
    private let systemSynth = AVSpeechSynthesizer()

    // MARK: - Available Voices
    static let voices: [String: String] = [
        "en-default":  "tts_models/en/ljspeech/tacotron2-DDC",
        "en-vctk":     "tts_models/en/vctk/vits",
        "en-jenny":    "tts_models/en/jenny/jenny",
        "multi-xtts":  "tts_models/multilingual/multi-dataset/xtts_v2",
        "de-thorsten": "tts_models/de/thorsten/tacotron2-DDC",
        "es-css10":    "tts_models/es/css10/vits",
    ]

    // MARK: - Init

    init(serverHost: String = "127.0.0.1", serverPort: Int = 9898) {
        self.serverURL = URL(string: "ws://\(serverHost):\(serverPort)")!
        self.session = URLSession(configuration: .default)

        audioEngine.attach(playerNode)
        audioEngine.connect(playerNode, to: audioEngine.mainMixerNode, format: nil)
        do {
            try audioEngine.start()
        } catch {
            lastError = "Audio engine failed: \(error.localizedDescription)"
        }

        connectWebSocket()
    }

    // MARK: - WebSocket Connection

    func connectWebSocket() {
        webSocket?.cancel(with: .goingAway, reason: nil)
        let task = session.webSocketTask(with: serverURL)
        self.webSocket = task
        task.resume()
        listenForMessages()

        // Send ping to check Coqui readiness
        let ping = try? JSONSerialization.data(withJSONObject: ["type": "ping"])
        if let ping = ping {
            task.send(.string(String(data: ping, encoding: .utf8)!)) { [weak self] error in
                if let error = error {
                    self?.lastError = "WS send error: \(error.localizedDescription)"
                    self?.isReady = false
                }
            }
        }
    }

    private func listenForMessages() {
        webSocket?.receive { [weak self] result in
            guard let self = self else { return }
            switch result {
            case .success(let message):
                self.handleMessage(message)
                self.listenForMessages()
            case .failure(let error):
                DispatchQueue.main.async {
                    self.lastError = "WS receive error: \(error.localizedDescription)"
                    self.isReady = false
                }
            }
        }
    }

    private func handleMessage(_ message: URLSessionWebSocketTask.Message) {
        guard case .string(let text) = message,
              let data = text.data(using: .utf8),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let type = json["type"] as? String else { return }

        DispatchQueue.main.async { [weak self] in
            guard let self = self else { return }

            switch type {
            case "connected":
                let features = json["features"] as? [String] ?? []
                self.isReady = true
                if features.contains("coqui_tts") {
                    self.currentEngine = .coqui
                } else if json["piper"] as? Bool == true {
                    self.currentEngine = .piper
                } else {
                    self.currentEngine = .system
                }

            case "audio":
                // Server-synthesized audio (Coqui or Piper)
                if let b64 = json["data"] as? String, let audioData = Data(base64Encoded: b64) {
                    self.playAudioData(audioData)
                }
                self.processNext()

            case "coqui_done", "piper_done":
                let fallback = json["fallback"] as? Bool ?? false
                if fallback {
                    // Server engine unavailable — use system fallback
                    if let text = self.ttsQueue.first?.text {
                        self.speakWithSystem(text)
                    }
                }
                self.processNext()

            case "coqui_status":
                if let ready = json["ready"] as? Bool {
                    self.isReady = ready
                    if ready { self.currentEngine = .coqui }
                }

            case "error":
                self.lastError = json["code"] as? String ?? "Unknown error"
                self.processNext()

            default:
                break
            }
        }
    }

    // MARK: - Public API

    /// Enqueue text for speech synthesis with the current engine.
    func speak(_ text: String, voice: String = "en-default", speed: Float = 1.0) {
        guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }

        queueLock.lock()
        ttsQueue.append((text: text, voice: voice, speed: speed))
        queueLock.unlock()

        if !isProcessing {
            processNext()
        }
    }

    /// Clear the TTS queue and stop current playback.
    func stop() {
        queueLock.lock()
        ttsQueue.removeAll()
        isProcessing = false
        queueLock.unlock()

        playerNode.stop()
        systemSynth.stopSpeaking(at: .immediate)
        DispatchQueue.main.async { self.isSpeaking = false }
    }

    // MARK: - Queue Processing

    private func processNext() {
        queueLock.lock()
        guard !ttsQueue.isEmpty else {
            isProcessing = false
            queueLock.unlock()
            DispatchQueue.main.async { self.isSpeaking = false }
            return
        }
        isProcessing = true
        let item = ttsQueue.removeFirst()
        queueLock.unlock()

        DispatchQueue.main.async { self.isSpeaking = true }

        switch currentEngine {
        case .coqui:
            sendCoquiRequest(text: item.text, voice: item.voice, speed: item.speed)
        case .piper:
            sendPiperRequest(text: item.text)
        case .system:
            speakWithSystem(item.text, speed: item.speed)
        }
    }

    // MARK: - Engine Dispatch

    private func sendCoquiRequest(text: String, voice: String, speed: Float) {
        let msg: [String: Any] = [
            "type": "coqui_speak",
            "text": text,
            "voice": CoquiTTSService.voices[voice] ?? voice,
            "speed": speed,
        ]
        sendJSON(msg)
    }

    private func sendPiperRequest(text: String) {
        let msg: [String: Any] = [
            "type": "piper_speak",
            "text": text,
        ]
        sendJSON(msg)
    }

    private func sendJSON(_ dict: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: dict),
              let str = String(data: data, encoding: .utf8) else {
            processNext()
            return
        }
        webSocket?.send(.string(str)) { [weak self] error in
            if let error = error {
                DispatchQueue.main.async {
                    self?.lastError = "Send failed: \(error.localizedDescription)"
                }
                // Fallback to system TTS
                if let text = dict["text"] as? String {
                    self?.speakWithSystem(text)
                }
                self?.processNext()
            }
        }
    }

    // MARK: - Audio Playback

    private func playAudioData(_ data: Data) {
        guard let tempURL = writeTempWAV(data) else {
            processNext()
            return
        }
        do {
            let audioFile = try AVAudioFile(forReading: tempURL)
            playerNode.stop()
            playerNode.scheduleFile(audioFile, at: nil) { [weak self] in
                try? FileManager.default.removeItem(at: tempURL)
                // processNext() is called from handleMessage after audio type
            }
            playerNode.play()
        } catch {
            lastError = "Playback error: \(error.localizedDescription)"
            try? FileManager.default.removeItem(at: tempURL)
        }
    }

    private func writeTempWAV(_ data: Data) -> URL? {
        let url = FileManager.default.temporaryDirectory
            .appendingPathComponent("coqui_\(UUID().uuidString).wav")
        do {
            try data.write(to: url)
            return url
        } catch {
            lastError = "Write temp file error: \(error.localizedDescription)"
            return nil
        }
    }

    // MARK: - System Fallback

    private func speakWithSystem(_ text: String, speed: Float = 1.0) {
        let utterance = AVSpeechUtterance(string: text)
        utterance.rate = speed * AVSpeechUtteranceDefaultSpeechRate
        utterance.voice = AVSpeechSynthesisVoice(language: "en-US")
        systemSynth.speak(utterance)
        // System synth is fire-and-forget; queue continues after send
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
            self?.processNext()
        }
    }
}
