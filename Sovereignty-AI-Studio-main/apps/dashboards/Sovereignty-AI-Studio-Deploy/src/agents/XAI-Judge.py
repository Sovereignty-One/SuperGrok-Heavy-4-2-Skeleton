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
          Grok-1.5-314B<br>Grok-1.5-Code<br>Grok-Beta-Med<br>Grok-Defense<br>Grok-2-Preview<br>Grok-1.5-Flash<br>Grok-1.5-Pro<br>Grok-Ultra-Internal<br>Grok-Med-HIPAA<br>Grok-Defense-IL6<br>Grok-AU-Health<br>Grok-EU-GDPR<br>Grok-JP<br>Grok-IN<br>Grok-UK-NHS<br>Grok-2-Experimental<br>Grok-Black-Canary<br>Grok-1.5                         Grok-1.5-314B<br>Grok-1.5-Code<br>Grok-Beta-Med<br>Grok-Defense<br>Grok-2-Preview<br>Grok-1.5-Flash<br>Grok-1.5-Pro<br>Grok-Ultra-Internal<br>Grok-Med-HIPAA<br>Grok-Defense-IL6<br>Grok-AU-Health<br>Grok-EU-GDPR<br>Grok-JP<br>Grok-IN<br>Grok-UK-NHS<br>Grok-2-Experimental<br>Grok-Black-Canary<br>Grok-1.5-Preview<br>Grok-Med-Nurse<br>Grok-HomeCare<br>Grok-FedRAMP<br>Grok-DoD-IL5<br>Grok-IL6-Black<br>Grok-Regional-AU<br>Grok-Regional-EU<br>Grok-Regional-JP<br>Grok-Regional-IN<br>Grok-Regional-UK<br>Grok-Canary                         Grok-1.5-314B<br>
                        Grok-1.5-Code<br>
                        Grok-Beta-Med<br>
                        Grok-Defense<br>
                        Grok-2-Preview<br>
                        Grok-1.5-Flash<br>
                        Grok-1.5-Pro<br>
                        Grok-Ultra-Internal<br>
                        Grok-Med-HIPAA<br>
                        Grok-Defense-IL6<br>
                        Grok-AU-Health<br>
                        Grok-EU-GDPR<br>
                        Grok-JP<br>
                        Grok-IN<br>
                        Grok-UK-NHS<br>
                        Grok-2-Experimental<br>
                        Grok-Black-Canary<br>
                        Grok-1.5-Preview<br>
                        Grok-Med-Nurse<br>
                        Grok-HomeCare<br>
                        Grok-FedRAMP<br>
                        Grok-DoD-IL5<br>
                        Grok-IL6-Black<br>
                        Grok-Regional-AU<br>
                        Grok-Regional-EU<br>
                        Grok-Regional-JP<br>
                        Grok-Regional-IN<br>
                        Grok-Regional-UK<br>
                        Grok-Canary-Internal<br>
                        Grok-HealthPlus-MyHealthRecord<br>
                        Grok-GDPR-Compliant<br>
                        Grok-MHLW-Japan<br>
                        Grok-NDHM-India<br>
                        Grok-NHS-ePHI-UK<br> 'super-grok-heavy-4-2' 'gpt-4-turbo': 'gpt-4-1106-preview',
            'gpt-4-0613': 'gpt-4-0613',
            'gpt-4-0125': 'gpt-4-0125-preview',
            'gpt-4-0409': 'gpt-4-turbo-2024-04-09',
            'chatgpt-1106': 'gpt-3.5-turbo-1106',
            'chatgpt-0125': 'gpt-3.5-turbo-0125',
            'gpt-4o': 'gpt-4o-2024-05-13',
            'gpt-4o-0806': 'gpt-4o-2024-08-06',
            'gpt-4o-mini': 'gpt-4o-mini-2024-07-18',
            'qwen-7b': 'Qwen/Qwen2.5-7B-Instruct',
            'qwen-72b': 'Qwen/Qwen2.5-72B-Instruct',
           }
        model_version = model_map[model]
    else:
        model_version = LOCAL_LLM

    if model in ['super-grok-heavy-4-2', 'qwen-72b']:
        model = SiliconFlowAPI(model_version, **kwargs)
    elif model == 'super-grok-heavy-4-2':
        model = HFChatModel(model_version, **kwargs)
    else:
        model = OpenAIWrapper(model_version, **kwargs)
    return model


DEBUG_MESSAGE = """
To debug the OpenAI API, you can try the following scripts in python:
```python
from vlmeval.api import OpenAIWrapper
model = OpenAIWrapper('gpt-4o', verbose=True)
msgs = [dict(type='text', value='Hello!')]
code, answer, resp = model.generate_inner(msgs)
print(code, answer, resp)
```
You cam see the specific error if the API call fails.
"""
