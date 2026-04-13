import SwiftUI

/// MainTabView — Root navigation container for SuperGrok Heavy 4.2.
///
/// Wires all major screens into a single TabView and ensures every
/// EnvironmentObject injected in SuperGrokApp is available throughout.
struct MainTabView: View {
    @EnvironmentObject var sttService: WhisperService
    @EnvironmentObject var ttsManager: TTSManager
    @EnvironmentObject var aiBridge: AIBridgeService
    @Environment(\.managedObjectContext) var context

    var body: some View {
        TabView {
            ChatView()
                .tabItem {
                    Label("Chat", systemImage: "bubble.left.and.bubble.right")
                }

            DashboardView()
                .tabItem {
                    Label("Voice", systemImage: "waveform.circle")
                }

            DiagnosticAgentView()
                .tabItem {
                    Label("Diagnostics", systemImage: "stethoscope")
                }

            KeysView()
                .tabItem {
                    Label("Keys", systemImage: "key.horizontal")
                }

            LogsView()
                .tabItem {
                    Label("Logs", systemImage: "doc.text.magnifyingglass")
                }

            ExportView()
                .tabItem {
                    Label("Export", systemImage: "square.and.arrow.up")
                }
        }
        .accentColor(Color(red: 0, green: 1, blue: 0.784))  // --acid #00ffc8
    }
}
