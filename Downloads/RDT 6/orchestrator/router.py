import os
from digital_twin.utils.config import get_model_key

def pick(intent: str, ctx_tokens: int) -> str:
    """Route to appropriate model based on intent and context."""
    from digital_twin.utils.config import get_settings, is_production
    
    settings = get_settings()
    
    # Use GPT-3.5 for <12k tokens (as per requirements)
    is_heavy = ctx_tokens >= 12_000 or intent in {"INSIGHT", "COMPARISON", "specific_topic"}
    
    if is_heavy:
        if is_production():
            return os.getenv("DEPLOYMENT_GPT4_1", "MODEL_GPT4")
        else:
            return settings.LLM_HEAVY
    else:
        if is_production():
            return os.getenv("DEPLOYMENT_GPT35", "MODEL_GPT35")
        else:
            return settings.LLM_CHEAP 