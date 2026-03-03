struct ContentView: View {
    @State private var chainStatus = "🔴 OFFLINE"
    
    var body: some View {
        NavigationView {
            VStack(spacing: 30) {
                Text("CHAIN GATE")
                    .font(.title.bold())
                    .foregroundColor(.primary)
                
                Circle()
                    .fill(chainStatus == "🟢 LIVE" ? .green : .red)
                    .frame(width: 60, height: 60)
                    .overlay(Text(chainStatus).bold())
                
                Button("Connect to CSM") {
                    verifyAndConnect()
                }
                .buttonStyle(.borderedProminent)
                
                Button("ARM HONEYPOT") {
                    armHoney()
                }
                .buttonStyle(.bordered)
                .tint(.red)
                .foregroundColor(.white)
                .disabled(chainStatus != "🟢 LIVE")
            }
            .navigationTitle("Sovereignty Guard")
            .onAppear {
                chainStatus = verifyHardware() ? "🟢 LIVE" : "🔴 OFFLINE"
            }
        }
    }
}

func verifyHardware() -> Bool {
    let devId = UIDevice.current.identifierForVendor?.uuidString ?? ""
    let now = Date().timeIntervalSinceReferenceDate
    let drift = (now.truncatingRemainder(dividingBy: 1)) * 1000
    return drift <= 0.252 && devId.prefix(8) == "real-id-" // etched in keychain
}

func verifyAndConnect() {
    guard verifyHardware() else {
        UIImpactFeedbackGenerator(style: .heavy).impactOccurred()
        return
    }
    connectToCSM() // real socket, chain-signed
}

func armHoney() {
    Task {
        let hash = try? SHA3-512.hash(data: "honeypot_arm".data(using: .utf8)!).hex()
        try? await armHoneypot(hash: hash ?? "INVALID")
    }
}
