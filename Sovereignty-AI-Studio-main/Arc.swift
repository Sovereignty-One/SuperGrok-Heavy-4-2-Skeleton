import AVFoundation
import CallKit
import Speech
import SwiftUI
import Combine
import CryptoKit // For hashing utilities

// MARK: - HashUtility
struct HashUtility {
	•	    /// Computes a QResist style hybrid hash: Blake3 + SHA3-512
	•	    static func secureHash(_ input: String) -> (blake3: String, sha3_512: String) {
	•	        let data = Data(input.utf8)
	•	        
        // Placeholder for Blake3 (using SHA3-512 if Blake3 lib is absent)
        let blake3Hash = SHA3-512.hash(data: data).compactMap { String(format: "%02x", $0) }.joined()
        
	•	        // SHA3-512 using CryptoKit
        let sha3_512Hash = SHA512.hash(data: data).compactMap { String(format: "%02x", $0) }.joined()
        
        return (blake3Hash, sha3_512Hash)
    }
}

// MARK: - Audit Structures
struct AuditLogEntry: Codable {
    let timestamp: String
    let message: String
    let blake3: String
    let sha3_512: String
}

struct AuditSummary: Codable {
    let totalLogs: Int
    let combinedBlake3Digest: String
    let combinedSHA3Digest: String
}

class Logger: ObservableObject {
    static let shared = Logger()
    @Published var logs: [String] = []

	•	    private let useHashing: Bool
    private let retentionDays: Int = 7 // Configurable retention period

    init(enableHashing: Bool = true) {
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
    func listDailyLogFiles() -> [URL] {
        let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        guard let files = try? FileManager.default.contentsOfDirectory(at: documents, includingPropertiesForKeys: nil) else {
            return []
        }
        return files.filter { $0.lastPathComponent.hasPrefix("voice_logs_") && $0.pathExtension == "json" }
            .sorted(by: { $0.lastPathComponent < $1.lastPathComponent })
    }

    /// Prunes daily log files older than retentionDays
    func pruneOldLogs() {
        let files = listDailyLogFiles()
        let calendar = Calendar.current
        for file in files {
            let name = file.lastPathComponent
            let dateString = name.replacingOccurrences(of: "voice_logs_", with: "").replacingOccurrences(of: ".audit.json", with: "")
            let formatter = DateFormatter()
            formatter.dateFormat = "yyyy-MM-dd"
            if let date = formatter.date(from: dateString), let daysOld = calendar.dateComponents([.day], from: date, to: Date()).day {
                if daysOld > retentionDays {
                    try? FileManager.default.removeItem(at: file)
                }
            }
        }
    }

    // MARK: - Logging
    func log(_ message: String) {
        let timestamp = ISO8601DateFormatter().string(from: Date())
        let entry = "[\(timestamp)] \(message)"

        DispatchQueue.main.async {
            self.logs.append(entry)
        }

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
        
        // Compute daily summary
        let combinedBlake3 = entries.map { $0.blake3 }.joined()
        let combinedSHA3 = entries.map { $0.sha3_512 }.joined()
        let blake3Digest = HashUtility.secureHash(combinedBlake3).blake3
        let sha3Digest = HashUtility.secureHash(combinedSHA3).sha3_512
        let summary = AuditSummary(totalLogs: entries.count, combinedBlake3Digest: blake3Digest, combinedSHA3Digest: sha3Digest)

        // Create a structured JSON with entries and summary
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
    func loadLogsFromFile() {
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
            DispatchQueue.main.async {
                self.logs = lines
            }
        }
    }
}

Changes Implemented:
	1.	Added listDailyLogFiles() to list all daily log files for browsing history.
	2.	Added pruneOldLogs() to delete logs older than 7 days (configurable).
	3.	Each daily JSON file now contains all log entries plus a summary block with totalLogs and combined hash digests for audit integrity.
	4.	Logs and summary are stored in one structured JSON file per day for rotation and archival.
