import SwiftUI

/// DashboardView — Voice mode control using the unified TTSManager.
///
/// Displays the live Whisper transcript and lets the user toggle
/// continuous voice mode. All speech output is routed through
/// TTSManager so Coqui/Piper/System failover applies automatically.
struct DashboardView: View {
    @EnvironmentObject var sttService: WhisperService
    @EnvironmentObject var ttsManager: TTSManager

    @State private var continuousVoice = false

    var body: some View {
        NavigationView {
            VStack(spacing: 16) {
                Toggle("Continuous Voice Mode", isOn: $continuousVoice)
                    .padding(.horizontal)
                    .onChange(of: continuousVoice) { _, enabled in
                        if enabled {
                            sttService.startListening()
                        } else {
                            sttService.stopListening()
                        }
                    }

                // TTS engine status badge
                HStack {
                    Circle()
                        .fill(ttsManager.isConnected ? Color.green : Color.orange)
                        .frame(width: 8, height: 8)
                    Text(ttsManager.activeEngine)
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                }
                .padding(.horizontal)

                ScrollView {
                    Text(sttService.transcript.isEmpty
                         ? "Transcript will appear here…"
                         : sttService.transcript)
                        .font(.system(.body, design: .monospaced))
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding()
                }
                .background(Color(.systemGray6))
                .cornerRadius(12)
                .padding(.horizontal)

                Spacer()
            }
            .padding(.top)
            .navigationTitle("Voice")
            .onReceive(sttService.$transcript) { text in
                guard continuousVoice, !text.isEmpty else { return }
                ttsManager.speak("You said: \(text)")
            }
        }
    }
}
