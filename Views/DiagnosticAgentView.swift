import SwiftUI
import Combine

/// DiagnosticAgentView — Live error monitor and AI-powered fix suggestions.
///
/// Shows real-time connection status for all services (TTS, AI bridge,
/// WebSocket), displays errors as they occur, and lets you ask the
/// AI agent to diagnose and suggest fixes.
struct DiagnosticAgentView: View {
    @EnvironmentObject var aiBridge: AIBridgeService
    @EnvironmentObject var ttsManager: TTSManager

    @State private var selectedError: AIBridgeService.BridgeError?
    @State private var diagnosisResult: String = ""
    @State private var isDiagnosing = false
    @State private var customPrompt: String = ""

    var body: some View {
        NavigationView {
            List {
                // ── Status Section ──
                Section("Service Status") {
                    statusRow("WebSocket", connected: aiBridge.isConnected)
                    statusRow("TTS Engine", connected: ttsManager.isConnected,
                              detail: ttsManager.activeEngine)
                    ForEach(AIBridgeService.AIModel.allCases) { model in
                        statusRow(model.displayName,
                                  connected: aiBridge.connectionStatus[model] ?? false)
                    }
                }

                // ── Live Errors ──
                Section("Errors (\(aiBridge.errors.count))") {
                    if aiBridge.errors.isEmpty {
                        Label("No errors", systemImage: "checkmark.circle.fill")
                            .foregroundColor(.green)
                    } else {
                        ForEach(aiBridge.errors) { error in
                            errorRow(error)
                        }
                    }
                }

                // ── TTS Diagnostics ──
                Section("TTS Diagnostics (\(ttsManager.diagnostics.count))") {
                    if ttsManager.diagnostics.isEmpty {
                        Label("No TTS events", systemImage: "checkmark.circle.fill")
                            .foregroundColor(.green)
                    } else {
                        ForEach(ttsManager.diagnostics.prefix(20)) { entry in
                            HStack {
                                Circle()
                                    .fill(entry.level == .error ? .red :
                                          entry.level == .warning ? .orange : .blue)
                                    .frame(width: 8, height: 8)
                                VStack(alignment: .leading) {
                                    Text(entry.message)
                                        .font(.caption)
                                    Text(entry.timestamp, style: .time)
                                        .font(.caption2)
                                        .foregroundColor(.secondary)
                                }
                            }
                        }
                    }
                }

                // ── AI Diagnostic Agent ──
                Section("AI Diagnostic Agent") {
                    TextField("Describe a problem or paste an error...", text: $customPrompt, axis: .vertical)
                        .lineLimit(3...6)
                        .textFieldStyle(.roundedBorder)

                    Button(action: runDiagnosis) {
                        HStack {
                            if isDiagnosing {
                                ProgressView().scaleEffect(0.8)
                            } else {
                                Image(systemName: "stethoscope")
                            }
                            Text(isDiagnosing ? "Diagnosing..." : "Run Diagnosis")
                        }
                    }
                    .disabled(customPrompt.isEmpty && selectedError == nil)
                    .disabled(isDiagnosing)

                    if !diagnosisResult.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Label("Diagnosis", systemImage: "brain.head.profile")
                                .font(.headline)
                            Text(diagnosisResult)
                                .font(.system(.caption, design: .monospaced))
                                .padding(8)
                                .background(Color(.systemGray6))
                                .cornerRadius(8)
                        }
                    }
                }

                // ── Actions ──
                Section("Actions") {
                    Button("Reconnect All Services") {
                        aiBridge.connect()
                        ttsManager.reconnect()
                    }
                    Button("Clear Errors") {
                        aiBridge.clearErrors()
                    }
                    .foregroundColor(.red)
                    Button("Test TTS: Coqui") {
                        ttsManager.speak("Coqui TTS test. All systems nominal.", voice: "en-default")
                    }
                    Button("Test TTS: Piper") {
                        ttsManager.coquiService.currentEngine = .piper
                        ttsManager.speak("Piper TTS test. Voice synthesis active.")
                    }
                    Button("Test AI: Claude") {
                        aiBridge.query("Say hello in one sentence.", model: .claude)
                    }
                    Button("Test AI: GPT") {
                        aiBridge.query("Say hello in one sentence.", model: .gpt)
                    }
                    Button("Test AI: Grok") {
                        aiBridge.query("Say hello in one sentence.", model: .grok)
                    }
                }
            }
            .navigationTitle("Diagnostic Agent")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Circle()
                        .fill(aiBridge.isConnected ? .green : .red)
                        .frame(width: 12, height: 12)
                }
            }
        }
    }

    // MARK: - Components

    private func statusRow(_ name: String, connected: Bool, detail: String? = nil) -> some View {
        HStack {
            Circle()
                .fill(connected ? Color.green : Color.red)
                .frame(width: 10, height: 10)
            Text(name)
            Spacer()
            if let detail = detail {
                Text(detail)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            Text(connected ? "Online" : "Offline")
                .font(.caption)
                .foregroundColor(connected ? .green : .red)
        }
    }

    private func errorRow(_ error: AIBridgeService.BridgeError) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(.red)
                Text(error.model.displayName)
                    .font(.caption)
                    .bold()
                Spacer()
                Text(error.timestamp, style: .time)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
            Text(error.message)
                .font(.caption)
            if !error.suggestion.isEmpty {
                Label(error.suggestion, systemImage: "lightbulb.fill")
                    .font(.caption2)
                    .foregroundColor(.orange)
            }
            Button("Diagnose with AI") {
                selectedError = error
                customPrompt = error.message
                runDiagnosis()
            }
            .font(.caption2)
            .buttonStyle(.bordered)
        }
        .padding(.vertical, 4)
    }

    // MARK: - Diagnosis

    private func runDiagnosis() {
        isDiagnosing = true
        diagnosisResult = ""

        let errorText = customPrompt.isEmpty ? (selectedError?.message ?? "") : customPrompt
        let context = """
        Platform: iOS (SuperGrok Heavy 4.2)
        Server: Unified_Server.js on port 9898
        TTS Engine: \(ttsManager.activeEngine)
        WS Connected: \(aiBridge.isConnected)
        Active Model: \(aiBridge.activeModel.displayName)
        Recent errors: \(aiBridge.errors.prefix(3).map(\.message).joined(separator: "; "))
        """

        aiBridge.diagnose(errorText, context: context)

        // Watch for response
        DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
            self.waitForDiagnosis()
        }
    }

    private func waitForDiagnosis(attempts: Int = 0) {
        if !aiBridge.lastResponse.isEmpty && !aiBridge.isStreaming {
            diagnosisResult = aiBridge.lastResponse
            isDiagnosing = false
        } else if attempts < 30 {
            DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
                self.waitForDiagnosis(attempts: attempts + 1)
            }
        } else {
            diagnosisResult = "Diagnosis timed out. Check server connection."
            isDiagnosing = false
        }
    }
}
