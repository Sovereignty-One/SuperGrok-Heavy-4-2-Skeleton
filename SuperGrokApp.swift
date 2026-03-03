import SwiftUI
@main
struct SuperGrokApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject var sttService = WhisperService()
    @StateObject var ttsService = PiperService()
    var body: some Scene {
        WindowGroup {
            MainTabView()
                .environmentObject(sttService)
                .environmentObject(ttsService)
        }
    }
}
