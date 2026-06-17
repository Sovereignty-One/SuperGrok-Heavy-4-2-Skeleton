# Upstream: Sovereignty AI Studio

This repository (`sovereignty-one/supergrok-heavy-4-2-skeleton`) is a lightweight skeleton
derivative of **[Appel420/Sovereignty-AI-Studio](https://github.com/Appel420/Sovereignty-AI-Studio)**.

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
git remote add upstream https://github.com/Appel420/Sovereignty-AI-Studio.git
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
  https://github.com/Appel420/Sovereignty-AI-Studio.git main --squash
```

## Configuration

See `.upstream` for the machine-readable upstream configuration.

## Local mirror push (recommended for this repo)

For local CI/CD sync to `Appel420/Sovereignty-AI-Studio` (without Actions), use:

```bash
cp ci-cd/local/local-cicd.env.example ci-cd/local/local-cicd.env
./ci-cd/local/deploy-local.sh
```

Set `TARGET_REPO_URL`, `TARGET_REMOTE_NAME`, and `TARGET_BRANCH` in `ci-cd/local/local-cicd.env` as needed. Leave `TARGET_BRANCH` blank to mirror the checked-out branch, and set it explicitly when running from a detached HEAD.
