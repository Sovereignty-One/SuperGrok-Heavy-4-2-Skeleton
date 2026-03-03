"""
Syntax Checker Service with Color-Coded Error Output
Validates Python code and provides structured error reports
with severity-based color coding for dashboard display.
"""
import ast
import logging
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# Color codes for frontend rendering
SEVERITY_COLORS = {
    ErrorSeverity.ERROR: "#EF4444",     # Red
    ErrorSeverity.WARNING: "#F59E0B",   # Amber
    ErrorSeverity.INFO: "#3B82F6",      # Blue
}


class SyntaxCheckerService:
    """
    Service for checking Python code syntax with color-coded error reporting.
    Designed for dashboard integration with structured error output.
    """

    def check_syntax(self, code: str, filename: str = "<input>") -> Dict[str, Any]:
        """
        Check Python code for syntax errors.

        Args:
            code: Python source code string
            filename: Optional filename for error messages

        Returns:
            Dictionary with check results, errors, and color coding
        """
        errors: List[Dict[str, Any]] = []

        # Check for syntax errors using ast.parse
        try:
            ast.parse(code, filename=filename)
        except SyntaxError as e:
            errors.append({
                "type": "SyntaxError",
                "message": str(e.msg) if e.msg else "Invalid syntax",
                "line": e.lineno,
                "column": e.offset,
                "severity": ErrorSeverity.ERROR.value,
                "color": SEVERITY_COLORS[ErrorSeverity.ERROR],
                "text": e.text.rstrip() if e.text else "",
            })

        # Check for common issues via compile
        if not errors:
            try:
                compile(code, filename, "exec")
            except SyntaxError as e:
                errors.append({
                    "type": "CompileError",
                    "message": str(e.msg) if e.msg else "Compilation error",
                    "line": e.lineno,
                    "column": e.offset,
                    "severity": ErrorSeverity.ERROR.value,
                    "color": SEVERITY_COLORS[ErrorSeverity.ERROR],
                    "text": e.text.rstrip() if e.text else "",
                })

        # Lint-level warnings (basic checks)
        warnings = self._check_warnings(code)
        errors.extend(warnings)

        return {
            "valid": len([e for e in errors if e["severity"] == "error"]) == 0,
            "errors": errors,
            "error_count": len([e for e in errors if e["severity"] == "error"]),
            "warning_count": len([e for e in errors if e["severity"] == "warning"]),
            "info_count": len([e for e in errors if e["severity"] == "info"]),
            "color_legend": {
                "error": SEVERITY_COLORS[ErrorSeverity.ERROR],
                "warning": SEVERITY_COLORS[ErrorSeverity.WARNING],
                "info": SEVERITY_COLORS[ErrorSeverity.INFO],
            },
        }

    def _check_warnings(self, code: str) -> List[Dict[str, Any]]:
        """Check for common code warnings."""
        warnings = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check for trailing whitespace
            if line != line.rstrip() and line.rstrip():
                warnings.append({
                    "type": "TrailingWhitespace",
                    "message": "Trailing whitespace",
                    "line": i,
                    "column": len(line.rstrip()) + 1,
                    "severity": ErrorSeverity.INFO.value,
                    "color": SEVERITY_COLORS[ErrorSeverity.INFO],
                    "text": line.rstrip(),
                })

            # Check for bare except
            if stripped == "except:":
                warnings.append({
                    "type": "BareExcept",
                    "message": "Bare except clause - consider catching specific exceptions",
                    "line": i,
                    "column": 1,
                    "severity": ErrorSeverity.WARNING.value,
                    "color": SEVERITY_COLORS[ErrorSeverity.WARNING],
                    "text": line.rstrip(),
                })

            # Check for eval usage
            if "eval(" in stripped:
                warnings.append({
                    "type": "SecurityWarning",
                    "message": "Use of eval() is a security risk",
                    "line": i,
                    "column": line.index("eval(") + 1,
                    "severity": ErrorSeverity.WARNING.value,
                    "color": SEVERITY_COLORS[ErrorSeverity.WARNING],
                    "text": line.rstrip(),
                })

            # Check for exec usage
            if "exec(" in stripped:
                warnings.append({
                    "type": "SecurityWarning",
                    "message": "Use of exec() is a security risk",
                    "line": i,
                    "column": line.index("exec(") + 1,
                    "severity": ErrorSeverity.WARNING.value,
                    "color": SEVERITY_COLORS[ErrorSeverity.WARNING],
                    "text": line.rstrip(),
                })

        return warnings

    def check_python(self, code: str, filename: str = "<input>") -> Dict[str, Any]:
        """
        Check Python code — test-compatible interface.

        Returns dict with success, errors count, and issues list.
        """
        result = self.check_syntax(code, filename)
        issues = result.get("errors", [])
        error_count = result.get("error_count", 0)
        return {
            "success": error_count == 0,
            "errors": error_count,
            "warnings": result.get("warning_count", 0),
            "info": result.get("info_count", 0),
            "issues": issues,
            "color_legend": result.get("color_legend", {}),
        }

    def format_coloured(self, report: Dict[str, Any]) -> str:
        """
        Format a check report as colour-coded text output.

        Uses ANSI colours for terminal and severity labels for logs.
        """
        lines = []
        if report.get("success", True) and not report.get("issues"):
            lines.append("\033[32m✓ No issues found\033[0m")
            return "\n".join(lines)

        for issue in report.get("issues", []):
            severity = issue.get("severity", "info").upper()
            msg = issue.get("message", "")
            line_no = issue.get("line", "?")
            color_code = {
                "ERROR": "\033[31m",
                "WARNING": "\033[33m",
                "INFO": "\033[34m",
            }.get(severity, "\033[0m")
            lines.append(
                f"{color_code}[{severity}]\033[0m Line {line_no}: {msg}"
            )
        return "\n".join(lines)

    def get_status(self) -> Dict[str, Any]:
        """Get syntax checker service status."""
        return {
            "service": "syntax_checker",
            "colour_coded": True,
            "supported_languages": ["python"],
            "severity_levels": ["error", "warning", "info"],
            "colors": {
                "error": SEVERITY_COLORS[ErrorSeverity.ERROR],
                "warning": SEVERITY_COLORS[ErrorSeverity.WARNING],
                "info": SEVERITY_COLORS[ErrorSeverity.INFO],
            },
        }


# Global instance
syntax_checker = SyntaxCheckerService()
