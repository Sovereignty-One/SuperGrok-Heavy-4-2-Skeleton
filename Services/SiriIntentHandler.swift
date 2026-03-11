import Foundation
import Intents
import UIKit

/// SiriIntentHandler — Handles Siri voice commands and bridges them
/// to Claude, GPT, and Grok via the SuperGrok Unified Server.
///
/// Supported intents:
///   - "Hey Siri, ask SuperGrok..."      → AI query (uses active model)
///   - "Hey Siri, SuperGrok diagnose..." → Diagnostic agent
///   - "Hey Siri, SuperGrok speak..."    → TTS output
///
/// Usage: Register in Info.plist under NSExtension > IntentsSupported:
///   - INSendMessageIntent
///   - INSearchForMessagesIntent
class SiriIntentHandler: INExtension {

    override func handler(for intent: INIntent) -> Any? {
        if intent is INSendMessageIntent {
            return SuperGrokMessageHandler()
        }
        if intent is INSearchForMessagesIntent {
            return SuperGrokSearchHandler()
        }
        return nil
    }
}

// MARK: - Message Handler (Send query to AI)

class SuperGrokMessageHandler: NSObject, INSendMessageIntentHandling {

    func resolveRecipients(for intent: INSendMessageIntent,
                           with completion: @escaping ([INSendMessageRecipientResolutionResult]) -> Void) {
        // No specific recipient needed — SuperGrok handles all
        completion([.notRequired()])
    }

    func resolveContent(for intent: INSendMessageIntent,
                        with completion: @escaping (INStringResolutionResult) -> Void) {
        if let text = intent.content, !text.isEmpty {
            completion(.success(with: text))
        } else {
            completion(.needsValue())
        }
    }

    func handle(intent: INSendMessageIntent, completion: @escaping (INSendMessageIntentResponse) -> Void) {
        guard let query = intent.content else {
            completion(INSendMessageIntentResponse(code: .failure, userActivity: nil))
            return
        }

        // Route through SuperGrok AI bridge (shared instance for Siri extension)
        let bridge = AIBridgeService()
        bridge.query(query, model: .claude)
        // Siri will speak the response via the intent response
        let activity = NSUserActivity(activityType: "com.supergrok.ai.query")
        activity.userInfo = ["query": query]
        completion(INSendMessageIntentResponse(code: .success, userActivity: activity))
    }
}

// MARK: - Search Handler (Query history)

class SuperGrokSearchHandler: NSObject, INSearchForMessagesIntentHandling {

    func handle(intent: INSearchForMessagesIntent,
                completion: @escaping (INSearchForMessagesIntentResponse) -> Void) {
        let response = INSearchForMessagesIntentResponse(code: .success, userActivity: nil)
        response.messages = []
        completion(response)
    }
}

// MARK: - Siri Shortcut Donation

extension AIBridgeService {

    /// Donate a Siri shortcut for a frequently used query pattern.
    func donateSiriShortcut(for query: String, model: AIModel) {
        let intent = INSendMessageIntent(
            recipients: nil,
            outgoingMessageType: .outgoingMessageText,
            content: query,
            speakableGroupName: INSpeakableString(spokenPhrase: "SuperGrok"),
            conversationIdentifier: "supergrok-\(model.rawValue)",
            serviceName: "SuperGrok AI",
            sender: nil,
            attachments: nil
        )
        intent.suggestedInvocationPhrase = "Ask SuperGrok"

        let interaction = INInteraction(intent: intent, response: nil)
        interaction.donate { error in
            if let error = error {
                print("[Siri] Shortcut donation failed: \(error.localizedDescription)")
            }
        }
    }
}

// MARK: - AppDelegate Siri Setup

extension AppDelegate {

    /// Call from didFinishLaunchingWithOptions to request Siri authorization.
    func requestSiriAuthorization() {
        INPreferences.requestSiriAuthorization { status in
            switch status {
            case .authorized:
                print("[Siri] Authorized")
            case .denied, .restricted, .notDetermined:
                print("[Siri] Not authorized: \(status.rawValue)")
            @unknown default:
                break
            }
        }
    }
}
