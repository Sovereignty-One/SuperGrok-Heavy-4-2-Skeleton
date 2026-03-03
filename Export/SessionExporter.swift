import Foundation
class SessionExporter {
    static func export(messages: [MessageEntity]) -> Data? {
        let encoder = JSONEncoder()
        return try? encoder.encode(messages)
    }
}
