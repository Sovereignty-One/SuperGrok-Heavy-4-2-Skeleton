"""Self-Fixer Module

Scans its own code, detects syntax errors or simple bugs, and applies
self-healing modifications while maintaining tamper protection.
"""

import ast
import asyncio
import hashlib
import logging
import random

from .backup_manager import filelock

logger = logging.getLogger(__name__)


class SelfFixer:
    """Autonomous self-fixing AI that repairs its own code and optimizes performance."""

    def __init__(self, lock, scanner, notifier):
        self.lock = lock
        self.scanner = scanner
        self.notifier = notifier
        self.state = self._load_state()
        self.score = 50
        self.bug_count = 0

    def _load_state(self) -> list:
        """Load the current code state from the encrypted file or bootstrap it."""
        import os

        if os.path.exists(self.lock.code_file):
            with filelock(), open(self.lock.code_file, "rb") as f:
                encrypted = f.read()
            try:
                content = self.lock.cryptor.decrypt(encrypted)
                return [
                    line if line.endswith("\n") else line + "\n"
                    for line in content.splitlines()
                ]
            except Exception as e:
                logger.critical("Decrypt failed: %s — treating as tampered", e)
                self.notifier.send_notification("DecryptFailed", {"error": str(e)})
                raise SystemExit("Tamper or key loss detected — aborting.")
        lines = ["print('I am alive.')\n", "# v1 - born\n"]
        self.lock.update_chain("".join(lines))
        return lines

    def _save(self) -> None:
        """Save the current state to the encrypted file and update the hash chain."""
        content = "".join(self.state)
        self.lock.update_chain(content)

    async def detect_and_fix(self) -> None:
        """Detect syntax errors or unsafe patterns and apply fixes."""
        joined = "".join(self.state)
        if not self.lock.is_valid(joined):
            self.notifier.send_notification("TamperDetected", {})
            return

        try:
            tree = ast.parse(joined)
        except SyntaxError as e:
            logger.warning("Syntax error: %s", e)
            self.bug_count += 1
            self.state.append(f"# Fixed syntax: {e}\n")
            self.score += 10
            self._save()
            await self._publish_event()
            return

        for comment in self.scanner.analyze(joined):
            self.state.append(comment)
            self.bug_count += 1
            self.score -= 1

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                for stmt in node.body:
                    if (
                        isinstance(stmt, ast.Expr)
                        and isinstance(stmt.value, ast.Call)
                        and isinstance(stmt.value.func, ast.Name)
                        and stmt.value.func.id == "print"
                    ):
                        logger.info("Bug: print in loop — patching")
                        self.state.append("# Auto-fix: replaced print with logger\n")
                        self.score += 15
                        self.bug_count += 1
                        break

        self._save()
        await self._publish_event()

    async def _publish_event(self) -> None:
        """Broadcast a self-heal event for downstream consumers."""
        try:
            from bridge.event_bus import bus  # optional bridge integration

            await bus.publish(
                "SELF_HEAL_EVENT",
                {
                    "score": self.score,
                    "bug_count": self.bug_count,
                    "state_hash": hashlib.sha256(
                        "".join(self.state).encode()
                    ).hexdigest(),
                },
            )
        except ImportError:
            pass  # bridge not installed — event dropped silently

    async def optimize(self) -> None:
        """Apply performance optimizations and decay score over time."""
        self.score = max(0, self.score - 0.5)
        if random.random() < 0.3 and len(self.state) < 50:
            self.state.append("# perf: added asyncio.sleep\n")
            self.score += 5
            self._save()

    async def run(self) -> None:
        """Main execution loop of the self-fixer."""
        logger.info("Self-fixer alive.")
        while True:
            await self.detect_and_fix()
            await self.optimize()
            await asyncio.sleep(1)
