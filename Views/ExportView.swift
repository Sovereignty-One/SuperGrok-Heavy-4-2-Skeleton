import SwiftUI
struct ExportView: View {
    @Environment(\.managedObjectContext) var context
    var body: some View {
        VStack {
            Button("Export Session") {
                let messages = try? context.fetch(MessageEntity.fetchRequest())
                if let jsonData = try? JSONEncoder().encode(messages) {
                    let checksum = CryptoService.sha3_512(String(data: jsonData, encoding: .utf8) ?? "")
                    let signature = CryptoService.signWithDilithium3(jsonData)
                    print("SHA3:", checksum)
                    print("Dilithium3 Signature:", signature.base64EncodedString())
                }
            }
        }
    }
}
