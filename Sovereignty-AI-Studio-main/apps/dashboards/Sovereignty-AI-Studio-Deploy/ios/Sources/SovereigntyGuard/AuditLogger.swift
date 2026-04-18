// AuditLogger.swift
// SovereigntyGuard
//
// Hash utilities and audit logging with daily rotation.

import Foundation
import CryptoKit

// MARK: - HashUtility
public struct HashUtility: Sendable {
    /// Computes a hybrid hash: SHA-256 (placeholder for Blake3) + SHA-512
    /// Note: Field names use `sha3_512` for compatibility with existing audit JSON format.
    public static func secureHash(_ input: String) -> (blake3: String, sha3_512: String) {
        let data = Data(input.utf8)

        // Placeholder for Blake3 (using SHA-256 as stand-in)
        let blake3Hash = SHA256.hash(data: data).compactMap { String(format: "%02x", $0) }.joined()

        // SHA-512
        let sha512Hash = SHA512.hash(data: data).compactMap { String(format: "%02x", $0) }.joined()

        return (blake3Hash, sha512Hash)
    }
}

// MARK: - Audit Structures
public struct AuditLogEntry: Codable, Sendable {
    public let timestamp: String
    public let message: String
    public let blake3: String
    public let sha3_512: String
}

public struct AuditSummary: Codable, Sendable {
    public let totalLogs: Int
    public let combinedBlake3Digest: String
    public let combinedSHA3Digest: String
}

@MainActor
public class AuditLogger: ObservableObject {
    public static let shared = AuditLogger()
    @Published public var logs: [String] = []

    private let useHashing: Bool
    private let retentionDays: Int = 7

    public init(enableHashing: Bool = true) {
        self.useHashing = enableHashing
    }

    // MARK: - File Management
    private func currentAuditFileURL() -> URL {
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        let currentDate = dateFormatter.string(from: Date())

        let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let dailyFile = "voice_logs_\(currentDate).audit.json"
        let dailyFileURL = documents.appendingPathComponent(dailyFile)

        if !FileManager.default.fileExists(atPath: dailyFileURL.path) {
            let emptyArray: [AuditLogEntry] = []
            if let data = try? JSONEncoder().encode(emptyArray) {
                try? data.write(to: dailyFileURL, options: .atomic)
            }
        }
        return dailyFileURL
    }

    /// Lists all daily audit files in the documents directory
    public func listDailyLogFiles() -> [URL] {
        let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        guard let files = try? FileManager.default.contentsOfDirectory(at: documents, includingPropertiesForKeys: nil) else {
            return []
        }
        return files.filter { $0.lastPathComponent.hasPrefix("voice_logs_") && $0.pathExtension == "json" }
            .sorted(by: { $0.lastPathComponent < $1.lastPathComponent })
    }

    /// Prunes daily log files older than retentionDays
    public func pruneOldLogs() {
        let files = listDailyLogFiles()
        let calendar = Calendar.current
        for file in files {
            let name = file.lastPathComponent
            let dateString = name.replacingOccurrences(of: "voice_logs_", with: "").replacingOccurrences(of: ".audit.json", with: "")
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd"
            if let date = formatter.date(from: dateString),
               let daysOld = calendar.dateComponents([.day], from: date, to: Date()).day {
                if daysOld > retentionDays {
                    try? FileManager.default.removeItem(at: file)
                }
            }
        }
    }

    // MARK: - Logging
    public func log(_ message: String) {
        let timestamp = ISO8601DateFormatter().string(from: Date())
        let entry = "[\(timestamp)] \(message)"

        self.logs.append(entry)

        var blake3 = ""
        var sha3_512 = ""
        if useHashing {
            (blake3, sha3_512) = HashUtility.secureHash(message)
        }

        let auditEntry = AuditLogEntry(timestamp: timestamp, message: message, blake3: blake3, sha3_512: sha3_512)
        appendJSONAuditEntry(auditEntry)

        print(entry)
    }

    private func appendJSONAuditEntry(_ entry: AuditLogEntry) {
        let fileURL = currentAuditFileURL()
        let decoder = JSONDecoder()
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted]

        var entries: [AuditLogEntry] = []
        if let data = try? Data(contentsOf: fileURL),
           let existingEntries = try? decoder.decode([AuditLogEntry].self, from: data) {
            entries = existingEntries
        }

        entries.append(entry)

        let combinedBlake3 = entries.map { $0.blake3 }.joined()
        let combinedSHA3 = entries.map { $0.sha3_512 }.joined()
        let blake3Digest = HashUtility.secureHash(combinedBlake3).blake3
        let sha3Digest = HashUtility.secureHash(combinedSHA3).sha3_512
        let summary = AuditSummary(totalLogs: entries.count, combinedBlake3Digest: blake3Digest, combinedSHA3Digest: sha3Digest)

        let structured: [String: Any] = [
            "entries": entries.map { [
                "timestamp": $0.timestamp,
                "message": $0.message,
                "blake3": $0.blake3,
                "sha3_512": $0.sha3_512
            ]},
            "summary": [
                "totalLogs": summary.totalLogs,
                "combinedBlake3Digest": summary.combinedBlake3Digest,
                "combinedSHA3Digest": summary.combinedSHA3Digest
            ]
        ]

        if let data = try? JSONSerialization.data(withJSONObject: structured, options: [.prettyPrinted]) {
            try? data.write(to: fileURL, options: .atomic)
        }
    }

    // MARK: - Load logs for UI
    public func loadLogsFromFile() {
        let fileURL = currentAuditFileURL()
        if let data = try? Data(contentsOf: fileURL),
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let entries = json["entries"] as? [[String: String]] {
            let lines = entries.compactMap { e in
                if let ts = e["timestamp"], let msg = e["message"] {
                    return "[\(ts)] \(msg)"
                }
                return nil
            }
            self.logs = lines
        }
    }
}
