"""
DSPy configuration for OpenAI GPT-4o-mini.
"""

import os
from typing import Optional

import dspy


# Global LM instance
_lm: Optional[dspy.LM] = None


def configure_dspy(
    model: str = "openai/gpt-4o-mini",
    api_key: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 2000,
) -> dspy.LM:
    """
    Configure DSPy with OpenAI language model.

    Args:
        model: Model identifier (default: openai/gpt-4o-mini)
        api_key: OpenAI API key (default: from OPENAI_API_KEY env var)
        temperature: Sampling temperature (default: 0.1 for deterministic)
        max_tokens: Max tokens in response

    Returns:
        Configured dspy.LM instance
    """
    global _lm

    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Set it or pass api_key parameter."
            )

    # GPT-5 reasoning models require special params
    is_reasoning_model = "gpt-5" in model.lower() or "o1" in model.lower() or "o3" in model.lower()
    if is_reasoning_model:
        temperature = 1.0
        max_tokens = max(max_tokens, 16000)

    _lm = dspy.LM(
        model=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    dspy.configure(lm=_lm)

    # Enable MLflow autolog for DSPy (MLflow 3.x)
    try:
        import mlflow
        mlflow.dspy.autolog()
        print("DSPy autolog enabled")
    except Exception as e:
        print(f"DSPy autolog not available: {e}")

    return _lm


def get_lm() -> Optional[dspy.LM]:
    """Get the configured LM instance."""
    return _lm


def is_configured() -> bool:
    """Check if DSPy is configured."""
    return _lm is not None
