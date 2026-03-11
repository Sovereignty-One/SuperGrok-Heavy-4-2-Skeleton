import UIKit
import Intents
class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        // Request Siri authorization for voice commands
        requestSiriAuthorization()
        return true
    }
}
