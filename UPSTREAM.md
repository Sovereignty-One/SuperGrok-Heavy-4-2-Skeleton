# Upstream: Sovereignty AI Studio

This repository (`sovereignty-one/supergrok-heavy-4-2-skeleton`) is a lightweight skeleton
derivative of **[appel420/sovereignty-ai-studio](https://github.com/appel420/sovereignty-ai-studio)**.

## Relationship

| Aspect | Skeleton | Studio |
|--------|----------|--------|
| Purpose | Portable iSH/a-Shell runtime | Full production platform |
| Python deps | stdlib only | 50+ packages |
| Node deps | `ws` only | `ws` only |
| TTS | Piper + Coqui | Piper |
| AI features | Richer (OPAR, Movie, Music, 3D CGI) | Core |
| Encryption | QuadRachet (4-layer) | Standard JWT/HMAC |
| Nested subtree | `Sovereignty-AI-Studio-main/` | (upstream) |

## Setting Up the Upstream Remote

```bash
# Add the upstream remote (one-time setup)
git remote add upstream https://github.com/appel420/sovereignty-ai-studio.git
git fetch upstream
```

## Syncing Changes from Sovereignty AI Studio

### Option A: Merge from upstream main
```bash
git fetch upstream
git merge upstream/main --allow-unrelated-histories -m "chore: sync from sovereignty-ai-studio upstream"
```

### Option B: Subtree pull (for the nested Sovereignty-AI-Studio-main/ directory)
```bash
git subtree pull --prefix=Sovereignty-AI-Studio-main \
  https://github.com/appel420/sovereignty-ai-studio.git main --squash
```

## Configuration

See `.upstream` for the machine-readable upstream configuration.
