import SwiftUI
import CoreData

struct ExportView: View {
    @Environment(\.managedObjectContext) var context

    var body: some View {
        VStack(spacing: 16) {
            Text("Session Export")
                .font(.headline)
            Button("Export Session") {
                exportSession()
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }

    private func exportSession() {
        let request = NSFetchRequest<MessageEntity>(entityName: "MessageEntity")
        request.sortDescriptors = [NSSortDescriptor(key: "timestamp", ascending: true)]
        guard let messages = try? context.fetch(request) else { return }

        // Build a JSON-serialisable array from NSManagedObject properties.
        let payload: [[String: Any]] = messages.map { msg in
            [
                "id":           (msg.id ?? UUID()).uuidString,
                "timestamp":    ISO8601DateFormatter().string(from: msg.timestamp ?? Date()),
                "role":         msg.role ?? "",
                "content":      msg.content ?? "",
                "model":        msg.model ?? "",
                "sha3Signature": msg.sha3Signature ?? "",
            ]
        }

        guard let jsonData = try? JSONSerialization.data(withJSONObject: payload,
                                                        options: .prettyPrinted),
              let jsonString = String(data: jsonData, encoding: .utf8)
        else { return }

        let checksum  = CryptoService.sha3_512(jsonString)
        let signature = CryptoService.signWithDilithium3(jsonData)

        print("SHA3-512:", checksum)
        print("Dilithium3 Signature:", signature.base64EncodedString())
    }
}
