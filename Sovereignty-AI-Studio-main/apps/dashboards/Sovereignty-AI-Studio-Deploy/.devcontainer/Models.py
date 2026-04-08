# models.py
from dataclasses import dataclass
from typing import Dict, List, Union

@dataclass(frozen=True)
class ModelEntry:
    name: str
    display_name: str

# Core Grok models
CORE_GROK_MODELS: List[ModelEntry] = [
    ModelEntry("Grok-1.5-314B", "Grok-1.5-314B"),
    ModelEntry("Grok-1.5-Code", "Grok-1.5-Code"),
		    ModelEntry("Grok-1.5-Flash", "Grok-1.5-Flash"),
    ModelEntry("Grok-1.5-Pro", "Grok-1.5-Pro"),
		    ModelEntry("Grok-1.5-Preview", "Grok-1.5-Preview"),
		    ModelEntry("Grok-5.2-Codex", "Grok-5.2-Codex"),  # Codex helper agent
		]
		
		# Medical models
		MEDICAL_MODELS: List[ModelEntry] = [
		    ModelEntry("Grok-Beta-Med", "Grok-Beta-Med"),
		    ModelEntry("Grok-HealthPlus-MyHealthRecord", "Grok-HealthPlus-MyHealthRecord"),
    ModelEntry("Grok-HomeCare", "Grok-HomeCare"),
		    ModelEntry("Grok-Med-HIPAA", "Grok-Med-HIPAA"),
    ModelEntry("Grok-Med-Nurse", "Grok-Med-Nurse"),
]

# Regional models
REGIONAL_MODELS: List[ModelEntry] = [
		    ModelEntry("Grok-AU-Health", "Grok-AU-Health"),
    ModelEntry("Grok-EU-GDPR", "Grok-EU-GDPR"),
		    ModelEntry("Grok-IN", "Grok-IN"),
    ModelEntry("Grok-JP", "Grok-JP"),
		    ModelEntry("Grok-MHLW-Japan", "Grok-MHLW-Japan"),
    ModelEntry("Grok-NDHM-India", "Grok-NDHM-India"),
		    ModelEntry("Grok-NHS-ePHI-UK", "Grok-NHS-ePHI-UK"),
		    ModelEntry("Grok-Regional-AU", "Grok-Regional-AU"),
    ModelEntry("Grok-Regional-EU", "Grok-Regional-EU"),
    ModelEntry("Grok-Regional-IN", "Grok-Regional-IN"),
    ModelEntry("Grok-Regional-JP", "Grok-Regional-JP"),
    ModelEntry("Grok-Regional-UK", "Grok-Regional-UK"),
		    ModelEntry("Grok-UK-NHS", "Grok-UK-NHS"),
		]
		
# Security models
SECURITY_MODELS: Dict[str, List[ModelEntry]] = {
    "Compliance": [
        ModelEntry("Grok-Black-Canary", "Grok-Black-Canary"),
        ModelEntry("Grok-Canary", "Grok-Canary"),
        ModelEntry("Grok-Canary-Internal", "Grok-Canary-Internal"),
        ModelEntry("Grok-Defense", "Grok-Defense"),
        ModelEntry("Grok-Defense-IL6", "Grok-Defense-IL6"),
        ModelEntry("Grok-DoD-IL5", "Grok-DoD-IL5"),
		        ModelEntry("Grok-FedRAMP", "Grok-FedRAMP"),
		        ModelEntry("Grok-GDPR-Compliant", "Grok-GDPR-Compliant"),
		        ModelEntry("Grok-IL6-Black", "Grok-IL6-Black"),
		        ModelEntry("Grok-Ultra-Internal", "Grok-Ultra-Internal"),
		    ],
    "Cryptography": [
        ModelEntry("Argon2", "Argon2"),
        ModelEntry("Blake3", "Blake3"),
        ModelEntry("ChaCha20", "ChaCha20"),
    ],
    "PostQuantum": [
        ModelEntry("Q-Resist", "Q-Resist"),
        ModelEntry("Dilithium", "Dilithium"),
        ModelEntry("Falcon512", "Falcon512"),
    ],
}

# GPT models combined into nested dictionary
		GPT_MODELS: Dict[str, List[ModelEntry]] = {
    "GPT-4": [
		        ModelEntry("gpt-4-0125", "gpt-4-0125-preview"),
        ModelEntry("gpt-4-0409", "gpt-4-turbo-2024-04-09"),
        ModelEntry("gpt-4-0613", "gpt-4-0613"),
        ModelEntry("gpt-4-turbo", "gpt-4-1106-preview"),
        ModelEntry("gpt-4o", "gpt-4o-2024-05-13"),
        ModelEntry("gpt-4o-0806", "gpt-4o-2024-08-06"),
        ModelEntry("gpt-4o-mini", "gpt-4o-mini-2024-07-18"),
    ],
		    "GPT-3.5": [
		        ModelEntry("chatgpt-0125", "gpt-3.5-turbo-0125"),
		        ModelEntry("chatgpt-1106", "gpt-3.5-turbo-1106"),
		    ],
    "GPT-5": [
        ModelEntry("gpt-5.2-codex", "gpt-5.2-codex"),
    ],
}

# Qwen models
		QWEN_MODELS: List[ModelEntry] = [
    ModelEntry("qwen-7b", "Qwen/Qwen2.5-7B-Instruct"),
    ModelEntry("qwen-72b", "Qwen/Qwen2.5-72B-Instruct"),
]

# constants.py
from enum import Enum
from typing import Dict, List, Union

from models import (
    ModelEntry,
    CORE_GROK_MODELS,
    MEDICAL_MODELS,
    REGIONAL_MODELS,
    SECURITY_MODELS,
    GPT_MODELS,
    QWEN_MODELS,
)

class ModelCategory(Enum):
    CORE_GROK = "Core Grok"
    MEDICAL = "Medical"
    SECURITY = "Security and Compliance"
    REGIONAL = "Regional / Legal"
    EXPERIMENTAL = "Experimental"
    GPT = "GPT Series"
		    QWEN = "Qwen Models"
		
CATEGORY_MODELS: Dict[ModelCategory, Union[List[ModelEntry], Dict[str, List[ModelEntry]]]] = {
    ModelCategory.CORE_GROK: CORE_GROK_MODELS,
    ModelCategory.MEDICAL: MEDICAL_MODELS,
    ModelCategory.SECURITY: SECURITY_MODELS,
    ModelCategory.REGIONAL: REGIONAL_MODELS,
    ModelCategory.GPT: GPT_MODELS,
    ModelCategory.QWEN: QWEN_MODELS,
}

def flatten_category_models() -> List[ModelEntry]:
    flat_list: List[ModelEntry] = []
    for models in CATEGORY_MODELS.values():
        if isinstance(models, dict):
            for sublist in models.values():
                flat_list.extend(sublist)
        else:
            flat_list.extend(models)
	    return flat_list
