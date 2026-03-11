#!/usr/bin/env python3
"""
Build Judge V2 — Model selection and wrapper for SuperGrok AI models.
"""
import os


INTERNAL = os.environ.get('INTERNAL', 0)


def build_judge(**kwargs):
    model = kwargs.pop('model', None)
    kwargs.pop('nproc', None)

    LOCAL_LLM = os.environ.get('LOCAL_LLM', None)

    # Model registry — maps friendly names to backend identifiers
    model_map = {
        'Grok-4.20-314B': 'Grok-4.20-314B',
        'Grok-4.20-Code': 'Grok-4.20-Code',
        'Grok-4.20-Med': 'Grok-4.20-Med',
        'Grok-4.20-Defense': 'Grok-4.20-Defense',
        'Grok-4.20-Preview': 'Grok-4.20-Preview',
        'Grok-4.20-Flash': 'Grok-4.20-Flash',
        'Grok-4.20-Pro': 'Grok-4.20-Pro',
        'Grok-4.20-Ultra-Internal': 'Grok-4.20-Ultra-Internal',
        'Grok-4.20-Med-HIPAA': 'Grok-4.20-Med-HIPAA',
        'Grok-4.20-Defense-IL6': 'Grok-4.20-Defense-IL6',
        'Grok-4.20-AU-Health': 'Grok-4.20-AU-Health',
        'Grok-4.20-EU-GDPR': 'Grok-4.20-EU-GDPR',
        'Grok-4.20-JP': 'Grok-4.20-JP',
        'Grok-4.20-IN': 'Grok-4.20-IN',
        'Grok-4.20-UK-NHS': 'Grok-4.20-UK-NHS',
        'Grok-4.20-Experimental': 'Grok-4.20-Experimental',
        'Grok-4.20-Black-Canary': 'Grok-4.20-Black-Canary',
        'Grok-4.20-Preview2': 'Grok-4.20-Preview2',
        'Grok-4.20-Med-Nurse': 'Grok-4.20-Med-Nurse',
        'Grok-4.20-HomeCare': 'Grok-4.20-HomeCare',
        'Grok-4.20-FedRAMP': 'Grok-4.20-FedRAMP',
        'Grok-4.20-DoD-IL5': 'Grok-4.20-DoD-IL5',
        'Grok-4.20-IL6-Black': 'Grok-4.20-IL6-Black',
        'Grok-4.20-Regional-AU': 'Grok-4.20-Regional-AU',
        'Grok-4.20-Regional-EU': 'Grok-4.20-Regional-EU',
        'Grok-4.20-Regional-JP': 'Grok-4.20-Regional-JP',
        'Grok-4.20-Regional-IN': 'Grok-4.20-Regional-IN',
        'Grok-4.20-Regional-UK': 'Grok-4.20-Regional-UK',
        'Grok-4.20-Canary-Internal': 'Grok-4.20-Canary-Internal',
        'Grok-4.20-HealthPlus-MyHealthRecord': 'Grok-4.20-HealthPlus-MyHealthRecord',
        'Grok-4.20-GDPR-Compliant': 'Grok-4.20-GDPR-Compliant',
        'Grok-4.20-MHLW-Japan': 'Grok-4.20-MHLW-Japan',
        'Grok-4.20-NDHM-India': 'Grok-4.20-NDHM-India',
        'Grok-4.20-NHS-ePHI-UK': 'Grok-4.20-NHS-ePHI-UK',
        'gpt-4.20-turbo': 'gpt-4.20-turbo',
        'gpt-4.20o': 'gpt-4.20o',
        'gpt-4.20o-mini': 'gpt-4.20o-mini',
        'qwen-7b-4.20': 'Qwen/Qwen4.20-7B-Instruct',
        'qwen-72b-4.20': 'Qwen/Qwen4.20-72B-Instruct',
        'super-grok-heavy-4-20': 'super-grok-heavy-4-20',
    }

    if LOCAL_LLM is not None:
        model_version = LOCAL_LLM
    elif model in model_map:
        model_version = model_map[model]
    else:
        raise ValueError(f"Unknown model: {model}. Available: {list(model_map.keys())}")

    return {"model": model, "model_version": model_version, **kwargs}