// ContentView.swift
// SovereigntyGuard
//
// SwiftUI main view for CHAIN GATE — hardware verification and honeypot controls.

#if canImport(UIKit)
import UIKit
#endif
import SwiftUI
import CryptoKit

public struct ContentView: View {
    @State private var chainStatus = "🔴 OFFLINE"

    public init() {}

    public var body: some View {
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
    #if canImport(UIKit)
    let devId = UIDevice.current.identifierForVendor?.uuidString ?? ""
    #else
    let devId = ""
    #endif
    let now = Date().timeIntervalSinceReferenceDate
    let drift = (now.truncatingRemainder(dividingBy: 1)) * 1000
    return drift <= 0.252 && devId.prefix(8) == "real-id-"
}

func verifyAndConnect() {
    guard verifyHardware() else {
        #if canImport(UIKit)
        UIImpactFeedbackGenerator(style: .heavy).impactOccurred()
        #endif
        return
    }
    connectToCSM()
}

func connectToCSM() {
    Task {
        do {
            let healthy = try await SovereigntyAPIClient.shared.healthCheck()
            if healthy {
                let status = try await SovereigntyAPIClient.shared.mobileStatus()
                print("[CSM] Connected — service: \(status["service"] ?? "unknown")")
            }
        } catch {
            print("[CSM] Connection failed: \(error)")
        }
    }
}

func armHoney() {
    Task {
        let data = "honeypot_arm".data(using: .utf8)!
        let hash = SHA512.hash(data: data).compactMap { String(format: "%02x", $0) }.joined()
        try? await armHoneypot(hash: hash)
    }
}

func armHoneypot(hash: String) async throws {
    _ = try await SovereigntyAPIClient.shared.armHoneypot(hash: hash)
    print("[Honeypot] Armed with hash: \(hash.prefix(16))...")
}
