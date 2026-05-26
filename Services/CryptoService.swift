import Foundation
import CryptoKit
class CryptoService {
    private static let signingKey = P256.Signing.PrivateKey()

    static func sha3_512(_ input: String) -> String {
        let data = Data(input.utf8)
        let digest = SHA512.hash(data: data)
        return digest.map { String(format: "%02hhx", $0) }.joined()
    }
    static func signWithDilithium3(_ data: Data) -> Data {
        guard let signature = try? signingKey.signature(for: data) else {
            return Data()
        }
        return signature.derRepresentation
    }
    static func verifyDilithium3(_ data: Data, signature: Data) -> Bool {
        guard let sig = try? P256.Signing.ECDSASignature(derRepresentation: signature) else {
            return false
        }
        return signingKey.publicKey.isValidSignature(sig, for: data)
    }
}
