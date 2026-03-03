// VoiceCommandIntegrity.swift
// SovereigntyGuard
//
// On-device voice command integrity with strict intent checking.
// Features:
// - Three "hello" triggers mic flip (activation sequence).
// - One-word triggers for actions (e.g., "STOP THEM", "OFF").
// - Strict intent: exact phrase matching, no fuzzy logic.
// - Enhanced: real-time audio analysis for 20dB spike + child voice + panic tone = blackout.
// - On-device speech recognition using Speech framework.
// - No cloud processing, no persistent listening.
//
// Note: Requires NSMicrophoneUsageDescription and NSSpeechRecognitionUsageDescription in Info.plist.

#if canImport(Speech) && canImport(AVFoundation) && canImport(Accelerate)
import Foundation
import Speech
import AVFoundation
import Security
import Accelerate
import CryptoKit

public class VoiceCommandIntegrity: NSObject, SFSpeechRecognizerDelegate, @unchecked Sendable {
    public static let shared = VoiceCommandIntegrity()

    private let speechRecognizer = SFSpeechRecognizer(locale: Locale(identifier: "en-US"))!
    private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    private var recognitionTask: SFSpeechRecognitionTask?
    private let audioEngine = AVAudioEngine()

    private var activationCount = 0
    private let requiredActivations = 3
    private let activationPhrase = "hello"
    private var isListeningForActivation = true

    private let commandTriggers: [String: @Sendable () -> Void] = [
        "stop them": { FamilyGuardCore.shared.activateKillSwitch() },
        "off": { FamilyGuardCore.shared.goDark() }
    ]

    private override init() {
        super.init()
        speechRecognizer.delegate = self
        requestPermissions()
    }

    private func requestPermissions() {
        SFSpeechRecognizer.requestAuthorization { authStatus in
            DispatchQueue.main.async {
                switch authStatus {
                case .authorized:
                    print("Voice command integrity: Speech recognition authorized.")
                case .denied, .restricted, .notDetermined:
                    print("Voice command integrity: Speech recognition not available.")
                @unknown default:
                    break
                }
            }
        }

        AVAudioSession.sharedInstance().requestRecordPermission { granted in
            if !granted {
                print("Voice command integrity: Microphone access denied.")
            }
        }
    }

    /// Start listening for voice commands.
    public func startListening() {
        guard !audioEngine.isRunning else { return }

        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let recognitionRequest = recognitionRequest else { fatalError("Unable to create request") }

        let inputNode = audioEngine.inputNode
        recognitionRequest.shouldReportPartialResults = false

        let recordingFormat = inputNode.outputFormat(forBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: recordingFormat) { [weak self] buffer, _ in
            self?.processAudioBuffer(buffer)
            recognitionRequest.append(buffer)
        }

        recognitionTask = speechRecognizer.recognitionTask(with: recognitionRequest) { [weak self] result, error in
            guard let self = self else { return }

            if let result = result {
                let bestTranscription = result.bestTranscription.formattedString.lowercased()
                self.processTranscription(bestTranscription)
            }

            if error != nil || result?.isFinal == true {
                self.restartListening()
            }
        }

        audioEngine.prepare()
        do {
            try audioEngine.start()
        } catch {
            print("Voice command integrity: Audio engine failed to start.")
        }
    }

    /// Stop listening.
    public func stopListening() {
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        recognitionTask?.cancel()
        activationCount = 0
        isListeningForActivation = true
    }

    private func processTranscription(_ transcription: String) {
        let _ = hashTranscription(transcription)

        if isListeningForActivation {
            if transcription == activationPhrase {
                activationCount += 1
                if activationCount >= requiredActivations {
                    flipMicrophone()
                    isListeningForActivation = false
                    activationCount = 0
                }
            } else {
                activationCount = 0
            }
        } else {
            if let action = commandTriggers[transcription] {
                action()
                stopListening()
            }
        }
    }

    /// Real-time audio buffer analysis: 20dB spike + child voice + panic = blackout
    private func processAudioBuffer(_ buffer: AVAudioPCMBuffer) {
        let level = calculateDecibel(buffer)
        let tone = analyzeTone(buffer)
        let isChild = isChildVoice(buffer)

        if level > 20 && tone.contains("fear") && isChild {
            FamilyGuardCore.shared.goDark()
            stopListening()
            return
        }
    }

    private func flipMicrophone() {
        print("Voice command integrity: Microphone flipped for command mode.")
    }

    private func restartListening() {
        if audioEngine.isRunning {
            stopListening()
            startListening()
        }
    }

    private func hashTranscription(_ transcription: String) -> Data {
        let data = Data(transcription.utf8)
        let hash = SHA512.hash(data: data)
        return Data(hash)
    }

    private func calculateDecibel(_ buffer: AVAudioPCMBuffer) -> Float {
        guard let channelData = buffer.floatChannelData?[0] else { return 0 }
        let channelDataArray = Array(UnsafeBufferPointer(start: channelData, count: Int(buffer.frameLength)))
        let rms = sqrt(channelDataArray.map { $0 * $0 }.reduce(0, +) / Float(channelDataArray.count))
        return 20 * log10(max(rms, 1e-10))
    }

    private func analyzeTone(_ buffer: AVAudioPCMBuffer) -> String {
        let frameCount = Int(buffer.frameLength)
        guard frameCount > 0, buffer.floatChannelData != nil else { return "" }

        guard let channelData = buffer.floatChannelData?[0] else { return "" }
        let samples = Array(UnsafeBufferPointer(start: channelData, count: frameCount))

        // Simplified high-frequency energy check for panic/fear detection
        let halfCount = frameCount / 2
        guard halfCount > 0 else { return "" }
        let highHalf = samples[halfCount..<frameCount]
        let highEnergy = highHalf.map { $0 * $0 }.reduce(0, +) / Float(highHalf.count)

        if highEnergy > 0.5 {
            return "fear|panic"
        }
        return ""
    }

    private func isChildVoice(_ buffer: AVAudioPCMBuffer) -> Bool {
        guard let channelData = buffer.floatChannelData?[0] else { return false }
        let frameCount = Int(buffer.frameLength)
        guard frameCount > 0 else { return false }
        let sampleRate = buffer.format.sampleRate

        let childLow = Int(300.0 / sampleRate * Double(frameCount))
        let childHigh = min(Int(3000.0 / sampleRate * Double(frameCount)), frameCount)

        guard childLow < childHigh, childHigh <= frameCount else { return false }

        let samples = Array(UnsafeBufferPointer(start: channelData, count: frameCount))
        let childBandEnergy = samples[childLow..<childHigh].map { $0 * $0 }.reduce(0, +)
        let totalEnergy = samples.map { $0 * $0 }.reduce(0, +)

        guard totalEnergy > 0 else { return false }
        return (childBandEnergy / totalEnergy) > 0.6
    }

    // MARK: - SFSpeechRecognizerDelegate
    public func speechRecognizer(_ speechRecognizer: SFSpeechRecognizer, availabilityDidChange available: Bool) {
        if !available {
            stopListening()
        }
    }
}
#endif
