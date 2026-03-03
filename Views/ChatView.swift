import SwiftUI
import CoreData
struct ChatView: View {
    @Environment(\.managedObjectContext) var context
    @State private var inputText: String = ""
    var body: some View {
        VStack {
            TextField("Type message...", text: $inputText).textFieldStyle(RoundedBorderTextFieldStyle()).padding()
            Button("Send") {
                let msg = MessageEntity(context: context)
                msg.id = UUID()
                msg.timestamp = Date()
                msg.role = "user"
                msg.content = inputText
                msg.model = "local-llm-q5"
                msg.sha3Signature = CryptoService.sha3_512(inputText + "user")
                try? context.save()
                inputText = ""
            }.padding()
        }
    }
}
