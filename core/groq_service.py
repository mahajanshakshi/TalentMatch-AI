"""Official Groq LLM integration service with JSON mode and Pydantic validation."""

import json
import logging
from typing import Type, TypeVar, List, Optional
from pydantic import BaseModel, ValidationError
from groq import Groq, GroqError, AuthenticationError, RateLimitError, APIConnectionError, NotFoundError

import config

logger = logging.getLogger(__name__)

__all__ = ["GroqService", "GroqServiceError", "get_accessible_chat_models"]

T = TypeVar("T", bound=BaseModel)

# Preferred high-capacity chat models in order of quality
PREFERRED_MODELS_ORDER = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "qwen/qwen3.8-27b",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-20b",
    "mixtral-8x7b-32768",
    "allam-2-7b",
]


class GroqServiceError(Exception):
    """Raised when Groq API communication or validation fails."""
    pass


def get_accessible_chat_models(api_key: Optional[str] = None) -> List[str]:
    """
    Fetch accessible text/chat models for the provided or environment API key.
    Filters out audio, guard, and non-chat models.
    """
    key = config.get_effective_groq_api_key(api_key)
    if not key or len(key) < 10 or key.startswith("your_"):
        return PREFERRED_MODELS_ORDER

    try:
        client = Groq(api_key=key)
        raw_models = client.models.list().data
        model_ids = [m.id for m in raw_models]

        # Filter out non-chat models (e.g. whisper, prompt-guard)
        chat_models = [
            m for m in model_ids
            if not any(excluded in m.lower() for excluded in ["whisper", "prompt-guard", "safeguard"])
        ]

        if not chat_models:
            return PREFERRED_MODELS_ORDER

        # Sort according to PREFERRED_MODELS_ORDER
        def sort_key(model_name: str) -> int:
            try:
                return PREFERRED_MODELS_ORDER.index(model_name)
            except ValueError:
                return 99

        chat_models.sort(key=sort_key)
        return chat_models

    except Exception as e:
        logger.debug("Could not fetch remote Groq models: %s", e)
        return PREFERRED_MODELS_ORDER


class GroqService:
    """Wrapper around official Groq Python SDK for structured outputs."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = config.get_effective_groq_api_key(api_key)
        self.model = model or config.get_configured_groq_model()
        self.temperature = config.GROQ_TEMPERATURE

        if not self.api_key:
            logger.warning("GroqService initialized without an API key.")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)

    def is_ready(self) -> bool:
        """Check if client is configured with an API key."""
        return self.client is not None and bool(self.api_key)

    def _get_fallback_model(self) -> Optional[str]:
        """Find an alternative accessible model if current model 404s."""
        try:
            accessible = get_accessible_chat_models(self.api_key)
            for m in accessible:
                if m != self.model:
                    return m
        except Exception:
            pass
        return "openai/gpt-oss-120b"

    def call_structured_json(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
        max_tokens: int = config.MAX_OUTPUT_TOKENS,
        allow_fallback: bool = True,
    ) -> T:
        """
        Invoke Groq LLM with temperature 0 and JSON mode, validating output against a Pydantic model.
        """
        if not self.is_ready():
            raise GroqServiceError(
                "Groq API Key is not configured. Please paste your GROQ_API_KEY into the .env file "
                "or provide it in the application sidebar."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            logger.info("Calling Groq LLM model='%s' with JSON mode...", self.model)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )

            raw_content = response.choices[0].message.content
            if not raw_content:
                raise GroqServiceError("Groq returned an empty response.")

            logger.debug("Raw Groq response received: %d characters", len(raw_content))

            # Parse JSON
            try:
                data = json.loads(raw_content)
            except json.JSONDecodeError as jde:
                logger.error("Failed to decode JSON from Groq response: %s", raw_content)
                raise GroqServiceError(f"Groq did not return valid JSON: {str(jde)}") from jde

            # Validate with Pydantic v2
            try:
                validated_obj = response_model.model_validate(data)
                return validated_obj
            except ValidationError as ve:
                logger.error("Pydantic validation error against %s: %s", response_model.__name__, ve.json())
                raise GroqServiceError(
                    f"Model output schema validation failed for {response_model.__name__}: {str(ve)}"
                ) from ve

        except (NotFoundError, GroqError) as e:
            err_msg = str(e)
            if allow_fallback and ("does not exist" in err_msg or "model_not_found" in err_msg or "404" in err_msg):
                fallback = self._get_fallback_model()
                if fallback and fallback != self.model:
                    logger.warning("Model '%s' not accessible (404). Retrying with fallback '%s'", self.model, fallback)
                    self.model = fallback
                    return self.call_structured_json(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        response_model=response_model,
                        max_tokens=max_tokens,
                        allow_fallback=False,
                    )
            logger.error("Groq API Error: %s", err_msg)
            raise GroqServiceError(f"Groq API error: {err_msg}") from e
        except AuthenticationError as e:
            logger.error("Groq Authentication Error: %s", str(e))
            raise GroqServiceError("Invalid Groq API Key. Please verify your GROQ_API_KEY in .env.") from e
        except RateLimitError as e:
            logger.error("Groq Rate Limit Exceeded: %s", str(e))
            raise GroqServiceError("Groq rate limit exceeded. Please wait a few moments and try again.") from e
        except APIConnectionError as e:
            logger.error("Groq Connection Error: %s", str(e))
            raise GroqServiceError("Failed to connect to Groq API. Please check your internet connection.") from e
        except Exception as e:
            if isinstance(e, GroqServiceError):
                raise
            logger.error("Unexpected error during Groq invocation: %s", str(e), exc_info=True)
            raise GroqServiceError(f"An unexpected error occurred during AI analysis: {str(e)}") from e
