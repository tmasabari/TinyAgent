from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .tinyagent import PreflightControls


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
    system_prompt: str


@dataclass(frozen=True)
class AgentConfig:
    max_iterations: int
    minify_enabled: bool
    minify_interval_tokens: int
    preflight: PreflightControls
    system_prompt: str
    strings: dict[str, str]
    models: dict[str, ModelConfig]


def load_config(path: str | Path) -> AgentConfig:
    data: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    p = data["preflight"]
    prompts = data["prompts"]
    models = {
        key: ModelConfig(
            name=value["model"], base_url=value["base_url"],
            temperature=float(value["temperature"]), top_p=float(value["top_p"]),
            top_k=int(value["top_k"]), max_tokens=int(value["max_tokens"]),
            thinking=bool(value["thinking"]),
            tool_call_parser=value["tool_call_parser"],
            reasoning_parser=value["reasoning_parser"],
            prefix_cache=bool(value["prefix_cache"]),
            system_prompt=value.get("system_prompt", "").strip(),
        )
        for key, value in data["models"].items()
    }
    return AgentConfig(
        max_iterations=int(data["agent"]["max_iterations"]),
        minify_enabled=bool(data["agent"]["context_minify"]["enabled"]),
        minify_interval_tokens=int(data["agent"]["context_minify"]["interval_tokens"]),
        system_prompt=prompts["system"].strip(),
        strings={k: str(v) for k, v in prompts.get("strings", {}).items()},
        preflight=PreflightControls(
            current_words=frozenset(p["current_words"]),
            file_phrases=frozenset(p["file_phrases"]),
            domain_words=frozenset(p["domain_words"]),
            state_words=frozenset(p["state_words"]),
        ),
        models=models,
    )
