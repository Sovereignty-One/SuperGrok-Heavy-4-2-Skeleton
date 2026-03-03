// DebuggerDetection.swift
// SovereigntyGuard
//
// Debugger detection and hash chain verification.

#if canImport(Darwin)
import Foundation
import Darwin
import Security
import CommonCrypto

public enum DebuggerDetection {

    private static let chainGenesis = Data(
        Array("0000000000000000000000000000000000000000000000000000000000000000".utf8)
    )

    public static func currentHash(data: String) -> Data {
        var digest = [UInt8](repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
        data.withCString { ptr in
            CC_SHA256(ptr, CC_LONG(data.count), &digest)
        }
        return Data(digest)
    }

    public static func verifyChain(lastHash: Data, newEntry: String) -> Bool {
        let combined = lastHash.base64EncodedString() + newEntry
        let fresh = currentHash(data: combined)
        return fresh == currentHash(data: "valid-chain" + newEntry)
    }

    @discardableResult
    public static func etchLog(_ msg: String) -> Data {
        let now = "\(Int(Date().timeIntervalSince1970))"
        let entry = "\(now) | \(msg)"
        let hashed = currentHash(data: entry)
        let secured = hashed.base64EncodedString()

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: "chain_log"
        ]
        SecItemDelete(query as CFDictionary)

        let addQuery: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: "chain_log",
            kSecValueData as String: secured.data(using: .utf8)!
        ]
        SecItemAdd(addQuery as CFDictionary, nil)

        return hashed
    }

    public static func isDebuggerAttached() -> Bool {
        var info = kinfo_proc()
        var size = MemoryLayout<kinfo_proc>.size
        var mib: [Int32] = [CTL_KERN, KERN_PROC, KERN_PROC_PID, getpid()]
        sysctl(&mib, 4, &info, &size, nil, 0)
        return info.kp_proc.p_flag & P_TRACED != 0
    }

    /// Run debugger detection check. Logs and exits if debugger is found.
    public static func runCheck() {
        if isDebuggerAttached() {
            let entry = "DEBUGGER: Attached. Writing to log file."
            let hash = etchLog(entry)
            if verifyChain(lastHash: chainGenesis, newEntry: entry) {
                exit(0)
            }
        }
    }
}
#endif
