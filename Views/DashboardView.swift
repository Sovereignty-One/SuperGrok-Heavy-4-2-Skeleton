import SwiftUI
struct DashboardView: View {
    @EnvironmentObject var sttService: WhisperService
    @EnvironmentObject var ttsService: PiperService
    @State private var continuousVoice = false
    var body: some View {
        VStack {
            Toggle("Continuous Voice Mode", isOn: $continuousVoice).padding()
            ScrollView { Text(sttService.transcript) }
        }
        .onChange(of: continuousVoice) { value in
            if value { sttService.startListening() } else { sttService.stopListening() }
        }
        .onReceive(sttService.$transcript) { text in
            if continuousVoice { ttsService.speak("You said: \(text)") }
        }
    }
}
