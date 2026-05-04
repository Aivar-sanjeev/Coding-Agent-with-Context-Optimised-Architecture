"""Token accounting, cost estimation, and simple success checks."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Protocol


class PricingSettings(Protocol):
    large_input_price_per_m: float
    large_output_price_per_m: float
    small_input_price_per_m: float
    small_output_price_per_m: float


@dataclass
class APICallRecord:
    model: str
    role: str  # "large" | "small"
    operation: str
    input_tokens: int
    output_tokens: int
    wall_time_s: float


@dataclass
class MetricsSession:
    settings: PricingSettings
    calls: list[APICallRecord] = field(default_factory=list)
    steps: int = 0
    started_at: float = field(default_factory=time.perf_counter)

    def log_call(
        self,
        *,
        model: str,
        role: str,
        operation: str,
        input_tokens: int,
        output_tokens: int,
        wall_time_s: float,
    ) -> None:
        self.calls.append(
            APICallRecord(
                model=model,
                role=role,
                operation=operation,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                wall_time_s=wall_time_s,
            )
        )

    def bump_step(self) -> None:
        self.steps += 1

    def total_input_tokens_large(self) -> int:
        return sum(
            c.input_tokens for c in self.calls if c.role == "large"
        )

    def total_output_tokens_large(self) -> int:
        return sum(
            c.output_tokens for c in self.calls if c.role == "large"
        )

    def total_tokens_small(self) -> tuple[int, int]:
        inp = sum(c.input_tokens for c in self.calls if c.role == "small")
        out = sum(c.output_tokens for c in self.calls if c.role == "small")
        return inp, out

    def estimated_cost_usd(self) -> float:
        s = self.settings
        cost = 0.0
        for c in self.calls:
            if c.role == "large":
                cost += (c.input_tokens / 1_000_000) * s.large_input_price_per_m
                cost += (c.output_tokens / 1_000_000) * s.large_output_price_per_m
            elif c.role == "small":
                cost += (c.input_tokens / 1_000_000) * s.small_input_price_per_m
                cost += (c.output_tokens / 1_000_000) * s.small_output_price_per_m
        return cost

    def time_to_completion_s(self) -> float:
        return time.perf_counter() - self.started_at

    def summary_dict(self) -> dict[str, Any]:
        si, so = self.total_tokens_small()
        return {
            "total_input_tokens_large": self.total_input_tokens_large(),
            "total_output_tokens_large": self.total_output_tokens_large(),
            "total_input_tokens_small": si,
            "total_output_tokens_small": so,
            "total_cost_usd_estimate": round(self.estimated_cost_usd(), 6),
            "steps_to_completion": self.steps,
            "time_to_completion_s": round(self.time_to_completion_s(), 3),
            "num_api_calls": len(self.calls),
        }


def usage_from_response(usage: Any) -> tuple[int, int]:
    if usage is None:
        return 0, 0
    inp = int(getattr(usage, "prompt_tokens", 0) or 0)
    out = int(getattr(usage, "completion_tokens", 0) or 0)
    return inp, out


def format_results_table(rows: list[dict[str, Any]]) -> str:
    """Markdown-friendly table for write-ups."""
    if not rows:
        return ""
    keys = list(rows[0].keys())
    header = "| " + " | ".join(keys) + " |"
    sep = "| " + " | ".join("---" for _ in keys) + " |"
    lines = [header, sep]
    for r in rows:
        cells = []
        for k in keys:
            v = r.get(k, "")
            if isinstance(v, (dict, list)):
                v = json.dumps(v, ensure_ascii=False)
            cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)
