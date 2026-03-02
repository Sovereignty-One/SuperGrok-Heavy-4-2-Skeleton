Here is the updated build_judge function with all relevant model mappings and references updated to version 4.20:

import os
from ...smp import load_env

INTERNAL = os.environ.get('INTERNAL', 0)

def build_judge(**kwargs):
    from ...api import OpenAIWrapper, SiliconFlowAPI, HFChatModel
    model = kwargs.pop('model', None)
    kwargs.pop('nproc', None)
    load_env()
    LOCAL_LLM = os.environ.get('LOCAL_LLM', None)
    if LOCAL_LLM is None:
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
        }
        model_version = model_map[model]
    else:
        model_version = LOCAL_LLM

    if model in ['super-grok-heavy-4-20', 'qwen-72b-4.20']:
        model = SiliconFlowAPI(model_version, **kwargs)
    elif model == 'super-grok-heavy-4-20':
        model = HFChatModel(model_version, **kwargs)
    else:
        model = OpenAIWrapper(model_version, **kwargs)
    return model

All instances of 4-2 or older model tags have been updated to 4.20.

Do you want me to also **update the DEBUG_MESSAGE example** to show usage with gpt-4.20?
