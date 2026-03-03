// SovereigntyAPIClient.swift
// SovereigntyGuard
//
// Network client for connecting the iPhone app to the Sovereignty AI Studio backend.
// All traffic goes through port 9898.

import Foundation
#if canImport(UIKit)
import UIKit
#endif

/// Connects to the Sovereignty AI Studio backend on port 9898.
public final class SovereigntyAPIClient: @unchecked Sendable {

    /// Shared singleton instance.
    public static let shared = SovereigntyAPIClient()

    /// Base URL for the backend API — defaults to local network on port 9898.
    public var baseURL: String {
        get { _baseURL }
        set { _baseURL = newValue }
    }
    private var _baseURL: String

    /// JWT bearer token set after login.
    public var authToken: String?

    private let session: URLSession

    public init(baseURL: String = "http://localhost:9898") {
        self._baseURL = baseURL
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 15
        config.timeoutIntervalForResource = 30
        self.session = URLSession(configuration: config)
    }

    // MARK: - Health & Status

    /// Check if the backend is reachable.
    public func healthCheck() async throws -> Bool {
        let data = try await get(path: "/health")
        if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let status = json["status"] as? String {
            return status == "healthy"
        }
        return false
    }

    /// Fetch mobile-specific service status.
    public func mobileStatus() async throws -> [String: Any] {
        let data = try await get(path: "/api/v1/mobile/status")
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw APIError.invalidResponse
        }
        return json
    }

    // MARK: - Authentication

    /// Login and store the JWT token.
    public func login(username: String, password: String) async throws -> String {
        let body: [String: Any] = ["username": username, "password": password]
        let data = try await post(path: "/api/v1/auth/login", body: body)
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let token = json["access_token"] as? String else {
            throw APIError.authenticationFailed
        }
        self.authToken = token
        return token
    }

    // MARK: - Alerts

    /// Fetch user alerts from the backend.
    public func getAlerts(limit: Int = 50) async throws -> [[String: Any]] {
        let data = try await get(path: "/api/v1/alerts/?limit=\(limit)")
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]] else {
            throw APIError.invalidResponse
        }
        return json
    }

    /// Create a new alert, optionally with TTS.
    public func createAlert(type: String, title: String, message: String,
                            severity: String = "medium", speak: Bool = false) async throws -> [String: Any] {
        let body: [String: Any] = [
            "type": type,
            "title": title,
            "message": message,
            "severity": severity,
        ]
        let speakParam = speak ? "?speak=true" : ""
        let data = try await post(path: "/api/v1/alerts/\(speakParam)", body: body)
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw APIError.invalidResponse
        }
        return json
    }

    // MARK: - Honeypot

    /// Arm the honeypot with a signed hash.
    public func armHoneypot(hash: String) async throws -> [String: Any] {
        let body: [String: Any] = ["action": "arm", "hash": hash]
        let data = try await post(path: "/api/v1/alerts/", body: [
            "type": "security",
            "title": "Honeypot Armed",
            "message": "Honeypot armed with hash: \(hash.prefix(16))...",
            "severity": "high",
            "source": "ios_sovereignty_guard",
        ])
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw APIError.invalidResponse
        }
        return json
    }

    // MARK: - HTTP Helpers

    private func get(path: String) async throws -> Data {
        guard let url = URL(string: "\(_baseURL)\(path)") else {
            throw APIError.invalidURL
        }
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        addAuth(to: &request)
        let (data, response) = try await session.data(for: request)
        try validateResponse(response)
        return data
    }

    private func post(path: String, body: [String: Any]) async throws -> Data {
        guard let url = URL(string: "\(_baseURL)\(path)") else {
            throw APIError.invalidURL
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        addAuth(to: &request)
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, response) = try await session.data(for: request)
        try validateResponse(response)
        return data
    }

    private func addAuth(to request: inout URLRequest) {
        if let token = authToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
    }

    private func validateResponse(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        switch http.statusCode {
        case 200...299:
            return
        case 401:
            throw APIError.authenticationFailed
        case 403:
            throw APIError.forbidden
        default:
            throw APIError.serverError(http.statusCode)
        }
    }

    // MARK: - Errors

    public enum APIError: Error, CustomStringConvertible {
        case invalidURL
        case invalidResponse
        case authenticationFailed
        case forbidden
        case serverError(Int)

        public var description: String {
            switch self {
            case .invalidURL: return "Invalid URL"
            case .invalidResponse: return "Invalid response from server"
            case .authenticationFailed: return "Authentication failed"
            case .forbidden: return "Access forbidden"
            case .serverError(let code): return "Server error: \(code)"
            }
        }
    }
}
