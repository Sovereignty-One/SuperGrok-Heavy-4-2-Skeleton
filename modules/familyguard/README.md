# FamilyGuard -- Integration Module

This directory is a git submodule referencing [appel420/familyguard](https://github.com/appel420/familyguard).

## Initialize

```bash
git submodule update --init modules/familyguard
```

## What FamilyGuard Provides

- **VoiceCommandIntegrity.swift** -- iOS/macOS on-device voice command engine with emergency kill-switch
- **companion.html** -- Browser-based encrypted screen capture (Web Crypto API, zero cloud)
- **fortress.html** -- Fortress Protocol reference (Argon2id + BLAKE3 + AES-256-GCM + Zstd)
- **Guard** -- Extended Fortress Protocol documentation

## Integration with SuperGrok Skeleton

FamilyGuard is a companion module -- it does NOT run inside the Node/Python server at runtime.

| Component | How to use |
|-----------|------------|
| `companion.html` | Serve via the skeleton's HTTP server at `/companion.html` |
| `fortress.html` | Serve as a standalone encrypted data sealing tool |
| Swift app | Build separately in Xcode targeting iOS 16+ / macOS 13+ |
