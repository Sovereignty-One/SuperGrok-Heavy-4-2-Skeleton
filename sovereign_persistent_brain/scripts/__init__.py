"""Script helpers for the sovereign persistent brain."""

from .dispatch_event import dispatch_event
from .handle_error import handle_error
from .hydrate_brain import hydrate_brain
from ._brain_store import signer
from .persist_brain import persist_brain
from .register_agent import register_agent
from .rotate_keys import rotate_keys
from .rotate_tokens import rotate_tokens
from .self_sustain_loop import self_sustain_loop

__all__ = [
    "dispatch_event",
    "handle_error",
    "hydrate_brain",
    "persist_brain",
    "register_agent",
    "rotate_keys",
    "rotate_tokens",
    "self_sustain_loop",
    "signer",
]
