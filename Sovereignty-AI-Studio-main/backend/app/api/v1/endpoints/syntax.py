"""
Syntax checker API endpoints with color-coded error output.
Validates Python code and provides structured error reports.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SyntaxCheckRequest(BaseModel):
    code: str
    filename: str = "<input>"


@router.post("/check", response_model=dict)
async def check_syntax(request: SyntaxCheckRequest):
    """
    Check Python code for syntax errors.

    Returns color-coded errors with severity levels:
    - error (red #EF4444): Syntax/compile errors
    - warning (amber #F59E0B): Security/style warnings
    - info (blue #3B82F6): Informational notices
    """
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    from app.services.syntax_checker_service import syntax_checker
    return syntax_checker.check_syntax(request.code, request.filename)


@router.get("/colors", response_model=dict)
async def get_error_colors():
    """Get the color coding scheme for error severities."""
    return {
        "colors": {
            "error": {"hex": "#EF4444", "name": "Red", "description": "Syntax/compile errors"},
            "warning": {"hex": "#F59E0B", "name": "Amber", "description": "Security/style warnings"},
            "info": {"hex": "#3B82F6", "name": "Blue", "description": "Informational notices"},
        }
    }
