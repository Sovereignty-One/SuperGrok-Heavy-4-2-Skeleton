from typing import Dict
from .models import ModelEntry
from .location import get_country_code  # we'll write this

COMPLIANCE_MAP: Dict = {
    "US": "Grok-DoD-IL5",       # FedRAMP, HIPAA
    "EU": "Grok-EU-GDPR",       # GDPR, no EU data flow
    "JP": "Grok-JP",            # MHLW, no health leak
    "IN": "Grok-NDHM-India",    # Aadhaar-safe, NDEM
    "AU": "Grok-AU-Health",     # My Health Record, ePHI
    "UK": "Grok-UK-NHS",        # NHS backbone
    "CN": "qwen-72b",           # fallback, no Grok in CN
    "BR": "Grok-Regional-EU",   # LGPD → treat like EU
}

def route_model() -> ModelEntry:
    country = get_country_code()
    model_name = COMPLIANCE_MAP.get(country, "Grok-1.5-Pro")  # safe default
    # Pull live from registry
    for cat in CATEGORY_MODELS.values():
        if isinstance(cat, dict):
            for sublist in cat.values():
                for m in sublist:
                    if m.name == model_name:
                        return m
        elif isinstance(cat, list):
            for m in cat:
                if m.name == model_name:
                    return m
    return ModelEntry("fallback", "Safe Local")
