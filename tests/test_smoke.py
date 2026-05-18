"""Smoke tests – verify key modules import and behave correctly."""

import hashlib
import json
import os
import tempfile

import pytest


# ---------------------------------------------------------------------------
# logging_utils.immutable_logger
# ---------------------------------------------------------------------------

class TestImmutableLogger:
    def test_import(self):
        from logging_utils.immutable_logger import ImmutableLogger
        assert ImmutableLogger is not None

    def test_append_and_verify(self, tmp_path):
        from logging_utils.immutable_logger import ImmutableLogger
        log = tmp_path / "test.jsonl"
        il = ImmutableLogger(str(log), secret_key="testsecret")
        il.append_log({"msg": "hello"})
        assert il.verify_integrity()

    def test_write_boot_entry(self, tmp_path):
        from logging_utils.immutable_logger import ImmutableLogger
        log = tmp_path / "boot.jsonl"
        il = ImmutableLogger(str(log))
        result = il.write_boot_entry("sys-1", chain_seed="abc")
        assert result is True

    def test_file_checksum_returns_hex(self, tmp_path):
        from logging_utils.immutable_logger import ImmutableLogger
        log = tmp_path / "chk.jsonl"
        il = ImmutableLogger(str(log))
        il.append_log({"x": 1})
        cs = il.file_checksum()
        assert len(cs) == 64
        int(cs, 16)  # must be valid hex


# ---------------------------------------------------------------------------
# selffixerai package
# ---------------------------------------------------------------------------

class TestSelfFixerAIImports:
    def test_package_import(self):
        import selffixerai
        assert selffixerai.__all__

    def test_notifications(self):
        from selffixerai.notifications import Notifier
        n = Notifier()
        assert callable(n.send_notification)

    def test_deep_scanner(self):
        from selffixerai.analysis.deep_scanner import DeepScanner
        ds = DeepScanner()
        results = ds.analyze("x = 1\n")
        assert isinstance(results, list)

    def test_main_entry_importable(self):
        import selffixerai
        assert callable(selffixerai.main.main)
