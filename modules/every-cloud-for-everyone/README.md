# Every Cloud For Everyone -- Integration Module

This directory is a git submodule referencing [appel420/every-cloud-for-everyone](https://github.com/appel420/every-cloud-for-everyone).

## Initialize

```bash
git submodule update --init modules/every-cloud-for-everyone
```

## What Every Cloud Provides

A Swift Package Manager library applying client-side encryption on top of 22 cloud providers:
- iCloud, Google Drive, OneDrive, Dropbox, AWS S3, Azure Blob, Nextcloud, and 15+ more
- Scrypt key derivation + AES-256-GCM encryption before any cloud upload
- BLAKE3 integrity digests stored locally
- QResist uplink kill-switch
- LockdownMode blocks all non-essential network traffic

## Integration with SuperGrok Skeleton

This Swift package is not executed by the Node server at runtime.
Reference `Cloud_fortress` docs for equivalent browser-JS implementation patterns.
