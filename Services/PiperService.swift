import Foundation
import AVFoundation
class PiperService: ObservableObject {
    private var audioEngine = AVAudioEngine()
    private var playerNode = AVAudioPlayerNode()
    init() {
        audioEngine.attach(playerNode)
        audioEngine.connect(playerNode, to: audioEngine.mainMixerNode, format: nil)
        try? audioEngine.start()
    }
    func speak(_ text: String) {
        let piperPath = Bundle.main.path(forResource: "piper", ofType: "")!
        let process = Process()
        process.executableURL = URL(fileURLWithPath: piperPath)
        process.arguments = ["--voice", Bundle.main.path(forResource: "voice_en", ofType: "bin")!, "--text", text, "--output", "/tmp/output.wav"]
        try? process.run()
        process.waitUntilExit()
        let url = URL(fileURLWithPath: "/tmp/output.wav")
        if let file = try? AVAudioFile(forReading: url) {
            playerNode.stop()
            playerNode.scheduleFile(file, at: nil)
            playerNode.play()
        }
    }
}
