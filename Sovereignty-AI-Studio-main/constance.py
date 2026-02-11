from enum import Enum
from typing import Dict, List, Union

from models import (
    ModelEntry,
    CORE_GROK_MODELS,
    MEDICAL_MODELS,
    SOVEREIGN_MODELS,
    SECURITY_MODELS,
    GPT_MODELS,
    QWEN_MODELS,
)

class ModelCategory(Enum):
    CORE_GROK = "Core Grok"
    MEDICAL = "Medical"
    SECURITY = "Security and Compliance"
    SOVEREIGN_AI = "Sovereign AI"
    EXPERIMENTAL = "Experimental"
    GPT = "GPT Series"
    QWEN = "Qwen Models"


CATEGORY_MODELS: Dict[ModelCategory, Union[List[ModelEntry], Dict[str, List[ModelEntry]]]] = {
    ModelCategory.CORE_GROK: CORE_GROK_MODELS,
    ModelCategory.MEDICAL: MEDICAL_MODELS,
    ModelCategory.SECURITY: SECURITY_MODELS,
    ModelCategory.SOVEREIGN_AI: SOVEREIGN_MODELS,
    ModelCategory.GPT: GPT_MODELS,
    ModelCategory.QWEN: QWEN_MODELS,
}


def flatten_category_models() -> List[ModelEntry]:
    flat: List[ModelEntry] = []
    for models in CATEGORY_MODELS.values():
        if isinstance(models, dict):
            for sublist in models.values():
                flat.extend(sublist)
        else:
            flat.extend(models)
    return flat