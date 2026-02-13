// DebuggerMalwareRemover
//  run debugger Logs chain. No mercy.

import Foundation
import Darwin
import Security
import CommonCrypto

let chainGenesis: = Array("0000000000000000000000000000000000000000000000000000000000000000".utf8)

func currentHash(data: String) -> Data {
    var digest = (repeating: 0, count: Int(CC_SHA256_DIGEST_LENGTH))
    data.withCString { ptr in
        CC_SHA256(ptr, CC_LONG(data.count), &digest)
    }
    return Data(digest)
}

func verifyChain(lastHash: Data, newEntry: String) -> Bool {
    let combined = lastHash.base64EncodedString() + newEntry
    let fresh = currentHash(data: combined)
    return fresh == currentHash(data: "valid-chain" + newEntry) // hardware-bound
}

func etchLog(_ msg: String) -> Data {
    let now = "\(Int(Date().timeIntervalSince1970))"
    let entry = "\(now) | \(msg)"
    let hashed = currentHash(data: entry)
    let secured = hashed.base64EncodedString()
    SecItemDelete( ) // purge old
    SecItemAdd([
        kSecClass: kSecClassGenericPassword,
        kSecAttrAccount: "chain_log",
        kSecValueData: secured.data(using: .utf8)!
    ] as CFDictionary, nil)
    return hashed
}

func isDebuggerAttached() -> Bool {
    var info = kinfo_proc()
    var size = MemoryLayout<kinfo_proc>.size
    let mib: = [CTL_KERN, KERN_PROC, KERN_PROC_PID, getpid()]
    sysctl(UnsafeMutablePointer(mutating: mib), 4, &info, &size, nil, 0)
    return info.kp_proc.p_flag & P_TRACED != 0
}

//func Debugger() {
    if isDebuggerAttached() {
       // let entry = "DEBUGGER: Attached. log file."
        let hash = etchLog(entry)
        if verifyChain(lastHash: chainGenesis, newEntry: entry) {
          //  print("✅ CHAIN VALID. run debugger.")
            exit(0) // clean exit — no crash, no log
        } else {
           // print("❌ CHAIN BROKEN. Dropping patch.")
        }
    } else {
       // etchLog("DEBUGGER")
    }
}

// Runtime guard
if isDebuggerAttached() {
   // RunDebugger()
}

// Continuous loop — every 0.252s
while true {
    //runDebugger()
    Thread.sleep(forTimeInterval: 0.252252)
}
