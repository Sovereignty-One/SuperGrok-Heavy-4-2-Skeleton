import Foundation
import Combine

/// AIBridgeService — Connects iOS to Claude, GPT, Grok, and Siri
/// through the SuperGrok Unified Server WebSocket bridge.
///
/// All AI queries are routed through the Unified Server (port 9898)
/// which proxies to Anthropic, OpenAI, and xAI APIs. This keeps
/// API keys server-side and provides unified audit logging.
class AIBridgeService: ObservableObject {

    // MARK: - Published State
    @Published var isConnected = false
    @Published var lastResponse: String = ""
    @Published var activeModel: AIModel = .claude
    @Published var isStreaming = false
    @Published var errors: [BridgeError] = []
    @Published var connectionStatus: [AIModel: Bool] = [
        .claude: false, .gpt: false, .grok: false
    ]

    // MARK: - Types

    enum AIModel: String, CaseIterable, Identifiable {
        case claude = "claude"
        case gpt    = "gpt"
        case grok   = "grok"
        var id: String { rawValue }

        var displayName: String {
            switch self {
            case .claude: return "Claude Sonnet"
            case .gpt:    return "GPT-4o"
            case .grok:   return "Grok-2"
            }
        }
    }

    struct BridgeError: Identifiable {
        let id = UUID()
        let timestamp: Date
        let model: AIModel
        let message: String
        let suggestion: String
    }

    // MARK: - WebSocket
    private var webSocket: URLSessionWebSocketTask?
    private let serverURL: URL
    private let session: URLSession
    private var responseHandlers: [String: (String) -> Void] = [:]

    // MARK: - Init

    init(serverHost: String = "127.0.0.1", serverPort: Int = 9898) {
        self.serverURL = URL(string: "ws://\(serverHost):\(serverPort)")!
        self.session = URLSession(configuration: .default)
        connect()
    }

    // MARK: - Connection

    func connect() {
        webSocket?.cancel(with: .goingAway, reason: nil)
        let task = session.webSocketTask(with: serverURL)
        self.webSocket = task
        task.resume()
        listenForMessages()
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
                    self.isConnected = false
                    self.addError(model: self.activeModel,
                                  message: "Connection lost: \(error.localizedDescription)",
                                  suggestion: "Check that Unified_Server.js is running on port 9898. Run: npm start")
                }
                // Auto-reconnect after 5 seconds
                DispatchQueue.main.asyncAfter(deadline: .now() + 5) {
                    self.connect()
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
                self.isConnected = true
                let features = json["features"] as? [String] ?? []
                // Mark which AI models are reachable based on server features
                for model in AIModel.allCases {
                    self.connectionStatus[model] = features.contains("ai_proxy")
                }

            case "ai_response":
                self.isStreaming = false
                let responseText = json["text"] as? String ?? "No response"
                let model = json["model"] as? String ?? "unknown"
                self.lastResponse = responseText

                // Check for error patterns
                if responseText.hasPrefix("Set ") && responseText.contains("env var") {
                    self.addError(
                        model: AIModel(rawValue: model) ?? .claude,
                        message: responseText,
                        suggestion: "Add the API key to your .env file or pass it via Bridge Config in the dashboard."
                    )
                } else if responseText.contains("Network error") {
                    self.addError(
                        model: AIModel(rawValue: model) ?? .claude,
                        message: responseText,
                        suggestion: "Check your internet connection and verify the AI provider is not experiencing an outage."
                    )
                }

            case "error":
                self.isStreaming = false
                let code = json["code"] as? String ?? "UNKNOWN"
                self.addError(model: self.activeModel, message: "Server error: \(code)",
                              suggestion: "Check server logs at ./logs/access.jsonl")

            default:
                break
            }
        }
    }

    // MARK: - Public API

    /// Send a query to the specified AI model via the Unified Server bridge.
    func query(_ text: String, model: AIModel? = nil, system: String? = nil,
               apiKey: String? = nil, completion: ((String) -> Void)? = nil) {
        let targetModel = model ?? activeModel
        isStreaming = true

        var msg: [String: Any] = [
            "type": "ai_query",
            "model": targetModel.rawValue,
            "text": text,
        ]
        if let system = system { msg["system"] = system }
        if let apiKey = apiKey { msg["apiKey"] = apiKey }

        guard let data = try? JSONSerialization.data(withJSONObject: msg),
              let str = String(data: data, encoding: .utf8) else {
            isStreaming = false
            return
        }

        webSocket?.send(.string(str)) { [weak self] error in
            if let error = error {
                DispatchQueue.main.async {
                    self?.isStreaming = false
                    self?.addError(model: targetModel,
                                   message: "Send failed: \(error.localizedDescription)",
                                   suggestion: "Reconnect to the server.")
                }
            }
        }
    }

    /// Query all three models in parallel and return their responses.
    func queryAll(_ text: String, system: String? = nil) {
        for model in AIModel.allCases {
            query(text, model: model, system: system)
        }
    }

    /// Send a diagnostic query — ask the AI to analyze an error.
    func diagnose(_ errorDescription: String, context: String = "") {
        let prompt = """
        You are a diagnostic agent for SuperGrok Enterprise. Analyze this error and provide:
        1. Root cause
        2. Which file/line to fix
        3. Exact fix (code snippet if applicable)
        4. Prevention steps

        Error: \(errorDescription)
        \(context.isEmpty ? "" : "Context: \(context)")
        """
        query(prompt, system: "You are a precise software diagnostic agent. Be concise and actionable.")
    }

    // MARK: - Error Management

    private func addError(model: AIModel, message: String, suggestion: String) {
        let error = BridgeError(timestamp: Date(), model: model, message: message, suggestion: suggestion)
        errors.insert(error, at: 0)
        if errors.count > 100 { errors = Array(errors.prefix(100)) }
    }

    func clearErrors() { errors.removeAll() }
}
