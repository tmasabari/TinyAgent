from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ModelConfig:
    name: str
    base_url: str
    temperature: float
    top_p: float
    top_k: int
    max_tokens: int
    thinking: bool
    tool_call_parser: str
    reasoning_parser: str
    prefix_cache: bool


@dataclass(frozen=True)
class AgentConfig:
    max_iterations: int
    current_words: frozenset[str]
    file_phrases: frozenset[str]
    domain_words: frozenset[str]
    state_words: frozenset[str]
    models: dict[str, ModelConfig]


def load_config(path: str | Path, model: str) -> AgentConfig:
    data: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    preflight = data["preflight"]
    models = {
        key: ModelConfig(name=value["model"], base_url=value["base_url"],
                         temperature=float(value["temperature"]), top_p=float(value["top_p"]),
                         top_k=int(value["top_k"]), max_tokens=int(value["max_tokens"]),
                         thinking=bool(value["thinking"]),
                         tool_call_parser=value["tool_call_parser"],
                         reasoning_parser=value["reasoning_parser"],
                         prefix_cache=bool(value["prefix_cache"]))
        for key, value in data["models"].items()
    }
    if model not in models:
        raise ValueError(f"unknown model profile: {model}")
    return AgentConfig(
        max_iterations=int(data["agent"]["max_iterations"]),
        current_words=frozenset(preflight["current_words"]),
        file_phrases=frozenset(preflight["file_phrases"]),
        domain_words=frozenset(preflight["domain_words"]),
        state_words=frozenset(preflight["state_words"]),
        models=models,
    )
