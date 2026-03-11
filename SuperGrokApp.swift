import SwiftUI
@main
struct SuperGrokApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject var sttService = WhisperService()
    @StateObject var ttsService = PiperService()
    @StateObject var ttsManager = TTSManager()
    @StateObject var aiBridge = AIBridgeService()
    var body: some Scene {
        WindowGroup {
            MainTabView()
                .environmentObject(sttService)
                .environmentObject(ttsService)
                .environmentObject(ttsManager)
                .environmentObject(aiBridge)
        }
    }
}
