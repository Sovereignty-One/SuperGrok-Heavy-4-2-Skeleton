"""Main entry point for the self-fixer AI package."""

import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SELFFIX] %(levelname)s %(message)s")


async def main() -> None:
    from selffixerai.analysis.deep_scanner import DeepScanner
    from selffixerai.core.backup_manager import BackupManager
    from selffixerai.core.self_fixer import SelfFixer
    from selffixerai.notifications import Notifier
    from selffixerai.security.encryption import CodeCryptor
    from selffixerai.security.tamper_lock import TamperHardLock

    cryptor = CodeCryptor()
    backup_mgr = BackupManager()
    notifier = Notifier()
    lock = TamperHardLock(cryptor, backup_mgr)
    scanner = DeepScanner()
    fixer = SelfFixer(lock, scanner, notifier)
    await fixer.run()


if __name__ == "__main__":
    asyncio.run(main())
