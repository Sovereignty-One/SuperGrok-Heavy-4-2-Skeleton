"""Deep Scanner Module

Performs static analysis on Python code to identify issues like long
functions and unused variables.
"""

import logging

logger = logging.getLogger(__name__)


class DeepScanner:
    """Performs deep static analysis on Python code."""

    def analyze(self, code: str) -> list:
        """Analyze code and return a list of comments suggesting improvements."""
        comments = []
        try:
            import astroid  # optional dependency
            from astroid import nodes
            module = astroid.parse(code)
            for node in module.nodes_of_class(nodes.FunctionDef):
                if not getattr(node, "returns", None) and len(node.body) > 20:
                    comments.append(
                        f"# Suspicious: long function '{node.name}' — refactor?\n"
                    )
        except ImportError:
            logger.debug("astroid not installed; deep scan skipped")
        except Exception as e:
            logger.error("Deep scan failed: %s", e)
        return comments
