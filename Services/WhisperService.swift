import Foundation
import Combine
class WhisperService: ObservableObject {
    @Published var transcript: String = ""
    private var process: Process?
    func startListening() {
        guard process == nil else { return }
        let whisperPath = Bundle.main.path(forResource: "whisper", ofType: "")!
        process = Process()
        process?.executableURL = URL(fileURLWithPath: whisperPath)
        process?.arguments = ["--model", Bundle.main.path(forResource: "ggml-q5_1", ofType: "bin")!]
        let pipe = Pipe()
        process?.standardOutput = pipe
        pipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            if let line = String(data: handle.availableData, encoding: .utf8) {
                DispatchQueue.main.async {
                    self?.transcript = line.trimmingCharacters(in: .whitespacesAndNewlines)
                }
            }
        }
        try? process?.run()
    }
    func stopListening() {
        process?.terminate()
        process = nil
    }
}
