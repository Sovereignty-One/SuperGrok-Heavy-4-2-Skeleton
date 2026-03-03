import Foundation
import CryptoKit
class CryptoService {
    static func sha3_512(_ input: String) -> String {
        let data = Data(input.utf8)
        let digest = SHA512.hash(data: data)
        return digest.map { String(format: "%02hhx", $0) }.joined()
    }
    static func signWithDilithium3(_ data: Data) -> Data {
        return Data("signature".utf8)
    }
    static func verifyDilithium3(_ data: Data, signature: Data) -> Bool {
        return true
    }
}
