"""Central configuration loaded from environment."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

# integrate.api.nvidia.com expects catalog model ids (e.g. meta/llama-3.1-8b-instruct),
# not a Build "function" / deployment UUID — those produce 404 "Function '…': Not found".
_MODEL_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\s*$",
    re.IGNORECASE,
)


def _assert_model_slug(env_name: str, value: str) -> str:
    v = (value or "").strip()
    if not v:
        raise RuntimeError(f"{env_name} is empty; set a catalog model id in .env")
    if _MODEL_UUID.match(v):
        raise RuntimeError(
            f"{env_name}={v!r} looks like a Build function/deployment UUID. "
            f"For {os.getenv('NVIDIA_BASE_URL', 'https://integrate.api.nvidia.com/v1').rstrip('/')!r} "
            "use an OpenAI-compatible model slug from the NVIDIA catalog "
            "(examples: meta/llama-3.1-8b-instruct, meta/llama-3.1-405b-instruct, "
            "nvidia/nemotron-nano-9b-v2). "
            "Copy the exact model id from the model card on build.nvidia.com, not a function UUID."
        )
    return v


@dataclass(frozen=True)
class Settings:
    nvidia_api_key: str
    nvidia_base_url: str
    large_model: str
    small_model: str
    large_input_price_per_m: float
    large_output_price_per_m: float
    small_input_price_per_m: float
    small_output_price_per_m: float
    max_orchestrator_steps: int
    read_file_max_lines_dual: int
    small_model_max_tokens_default: int


def get_settings() -> Settings:
    key = os.getenv("NVIDIA_API_KEY", "").strip()
    if not key:
        raise RuntimeError("NVIDIA_API_KEY is not set")

    base = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").rstrip(
        "/"
    )
    # Default: Meta Llama 3.1 70B on the public catalog. Nemotron-specific slugs
    # (e.g. nvidia/llama-3.1-nemotron-70b-instruct) often 404 as "Function … not found"
    # if your account does not have that deployment entitled.
    large = _assert_model_slug(
        "LARGE_MODEL",
        os.getenv("LARGE_MODEL", "meta/llama-3.1-70b-instruct"),
    )
    small = _assert_model_slug(
        "SMALL_MODEL",
        os.getenv("SMALL_MODEL", "meta/llama-3.1-8b-instruct"),
    )

    return Settings(
        nvidia_api_key=key,
        nvidia_base_url=base,
        large_model=large,
        small_model=small,
        large_input_price_per_m=float(
            os.getenv("LARGE_INPUT_PRICE_PER_M", "2.0")
        ),
        large_output_price_per_m=float(
            os.getenv("LARGE_OUTPUT_PRICE_PER_M", "2.0")
        ),
        small_input_price_per_m=float(
            os.getenv("SMALL_INPUT_PRICE_PER_M", "0.15")
        ),
        small_output_price_per_m=float(
            os.getenv("SMALL_OUTPUT_PRICE_PER_M", "0.15")
        ),
        max_orchestrator_steps=int(os.getenv("MAX_ORCHESTRATOR_STEPS", "40")),
        read_file_max_lines_dual=int(os.getenv("READ_FILE_MAX_LINES_DUAL", "400")),
        small_model_max_tokens_default=int(
            os.getenv("SMALL_MODEL_MAX_TOKENS_DEFAULT", "400")
        ),
    )
