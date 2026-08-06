"""Validate the supergrok-enterprise frontend build layer.

These tests run `node build.mjs` inside supergrok-enterprise/ and assert that
the produced dist/ tree is coherent, local-only, and contains no dead artifacts.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ENTERPRISE_DIR = Path(__file__).parent.parent / "supergrok-enterprise"
DIST_DIR = ENTERPRISE_DIR / "dist"


def _build():
    """Run build.mjs and return the completed process."""
    return subprocess.run(
        [sys.executable, "-c",
         "import subprocess, sys; r = subprocess.run(['node', 'build.mjs'], "
         "cwd=sys.argv[1], capture_output=True, text=True); "
         "sys.stdout.write(r.stdout); sys.stderr.write(r.stderr); sys.exit(r.returncode)",
         str(ENTERPRISE_DIR)],
        capture_output=True,
        text=True,
    )


@pytest.fixture(scope="module")
def build_result():
    """Run the build once for all tests in this module."""
    result = subprocess.run(
        ["node", "build.mjs"],
        cwd=str(ENTERPRISE_DIR),
        capture_output=True,
        text=True,
    )
    return result


class TestEnterpriseBuild:
    """Validate supergrok-enterprise build output."""

    def test_build_exits_zero(self, build_result):
        assert build_result.returncode == 0, (
            f"build.mjs failed:\n{build_result.stderr}"
        )

    def test_dist_index_html_exists(self, build_result):
        assert (DIST_DIR / "index.html").is_file()

    def test_dist_main_js_exists(self, build_result):
        assert (DIST_DIR / "src" / "main.js").is_file()

    def test_dist_crypto_service_exists(self, build_result):
        assert (DIST_DIR / "src" / "services" / "crypto.js").is_file()

    def test_dist_export_service_exists(self, build_result):
        assert (DIST_DIR / "src" / "services" / "export.js").is_file()

    def test_dist_nginx_conf_exists(self, build_result):
        assert (DIST_DIR / "nginx.conf").is_file()

    def test_no_dead_react_artifacts_in_dist(self, build_result):
        dead = [
            DIST_DIR / "src" / "main.jsx",
            DIST_DIR / "src" / "App.jsx",
            DIST_DIR / "vite.config.js",
            DIST_DIR / "tailwind.config.js",
            DIST_DIR / "postcss.config.js",
        ]
        for path in dead:
            assert not path.exists(), f"Dead artifact present in dist/: {path}"

    def test_main_js_imports_crypto_service(self, build_result):
        content = (ENTERPRISE_DIR / "src" / "main.js").read_text()
        assert "services/crypto" in content, (
            "src/main.js must import the local crypto service"
        )

    def test_index_html_references_main_js_not_jsx(self, build_result):
        content = (ENTERPRISE_DIR / "index.html").read_text()
        assert "main.js" in content
        assert "main.jsx" not in content

    def test_no_external_network_calls_in_main_js(self, build_result):
        content = (ENTERPRISE_DIR / "src" / "main.js").read_text()
        forbidden = ["fetch(", "XMLHttpRequest", "http://", "https://"]
        for term in forbidden:
            assert term not in content, (
                f"src/main.js must not make external network calls; found: {term!r}"
            )

    def test_crypto_service_uses_web_crypto(self, build_result):
        content = (ENTERPRISE_DIR / "src" / "services" / "crypto.js").read_text()
        assert "crypto.subtle" in content, (
            "crypto.js must use the browser Web Crypto API"
        )
        assert "fetch(" not in content, (
            "crypto.js must not make remote calls"
        )
