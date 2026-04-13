import SwiftUI
import CoreData

@main
struct SuperGrokApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    @StateObject var sttService = WhisperService()
    @StateObject var ttsManager = TTSManager()
    @StateObject var aiBridge   = AIBridgeService()

    let persistenceController = PersistenceController.shared

    var body: some Scene {
        WindowGroup {
            MainTabView()
                .environment(\.managedObjectContext, persistenceController.container.viewContext)
                .environmentObject(sttService)
                .environmentObject(ttsManager)
                .environmentObject(aiBridge)
        }
    }
}

// MARK: - Core Data stack

struct PersistenceController {
    static let shared = PersistenceController()

    let container: NSPersistentContainer

    private init() {
        container = NSPersistentContainer(name: "MessageEntity")
        container.loadPersistentStores { _, error in
            if let error = error {
                // In production replace with proper error handling / user-facing alert.
                print("[CoreData] Failed to load store: \(error.localizedDescription)")
            }
        }
        container.viewContext.automaticallyMergesChangesFromParent = true
    }
}
