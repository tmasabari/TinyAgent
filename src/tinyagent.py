from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
import re
from typing import Any, Callable, Protocol


class Source(str, Enum):
    FILE = "file"
    WEB = "web"
    DOMAIN = "domain"


class Operation(str, Enum):
    EDIT = "edit"
    OS = "os"
    WEB = "web"


@dataclass(frozen=True)
class Runtime:
    knowledge_cutoff: datetime
    current_datetime: datetime
    input_modalities: tuple[str, ...] = ("text",)
    os: str = "unknown"
    shell: str = "unknown"
    working_directory: str = "."


@dataclass(frozen=True)
class PreflightControls:
    current_words: frozenset[str]
    file_phrases: frozenset[str]
    domain_words: frozenset[str]
    state_words: frozenset[str]


@dataclass(frozen=True)
class Requirement:
    source: Source
    query: str
    reason: str


@dataclass(frozen=True)
class HookContext:
    kind: str
    payload: dict[str, Any]


class Hook(Protocol):
    def before(self, context: HookContext) -> Any: ...
    def after(self, context: HookContext, result: Any) -> Any: ...


class EventSink(Protocol):
    def publish(self, name: str, payload: dict[str, Any]) -> None: ...


class NullEvents:
    def publish(self, name: str, payload: dict[str, Any]) -> None:
        pass


FILE_RE = re.compile(r"(?:^|[\s\"'`(])((?:[\w.-]+/)*[\w.-]+\.(?:cs|fs|vb|js|ts|tsx|jsx|py|java|go|rs|cpp|c|h|json|yaml|yml|xml|sql|md|txt|csproj|sln|log))(?:$|[\s\"'`),])", re.I)
DATE_RE = re.compile(r"\b(20\d{2})(?:-(\d{1,2})(?:-(\d{1,2}))?)?\b")


def _contains_any(text: str, values: frozenset[str]) -> bool:
    return any(v in text.lower() for v in values)


def _contains_post_cutoff_date(text: str, cutoff: datetime) -> bool:
    for match in DATE_RE.finditer(text):
        year = int(match.group(1))
        month = int(match.group(2) or 1)
        day = int(match.group(3) or 1)
        candidate = datetime(year, month, day, tzinfo=cutoff.tzinfo)
        if candidate > cutoff:
            return True
    return False


def preflight(request: str, runtime: Runtime, controls: PreflightControls) -> list[Requirement]:
    requirements: list[Requirement] = []
    lower = request.lower()
    if _contains_any(lower, controls.current_words) or _contains_post_cutoff_date(request, runtime.knowledge_cutoff):
        requirements.append(Requirement(Source.WEB, request, "current_or_post_cutoff_information"))
    file_match = FILE_RE.search(request)
    if file_match:
        requirements.append(Requirement(Source.FILE, file_match.group(1), "local_artifact_reference"))
    elif _contains_any(lower, controls.file_phrases):
        requirements.append(Requirement(Source.FILE, request, "local_state_required"))
    if _contains_any(lower, controls.domain_words) and _contains_any(lower, controls.state_words):
        requirements.append(Requirement(Source.DOMAIN, request, "authoritative_live_or_domain_state"))
    return _dedupe(requirements)


def _dedupe(requirements: list[Requirement]) -> list[Requirement]:
    seen: set[tuple[Source, str]] = set()
    result: list[Requirement] = []
    for item in requirements:
        key = (item.source, item.query)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def runtime_prompt(runtime: Runtime) -> str:
    return (
        "[RUNTIME]\n"
        f"knowledge_cutoff={runtime.knowledge_cutoff.isoformat()}\n"
        f"current_datetime={runtime.current_datetime.isoformat()}\n"
        f"input_modalities={','.join(runtime.input_modalities)}\n"
        f"os={runtime.os}\n"
        f"shell={runtime.shell}\n"
        f"working_directory={runtime.working_directory}\n"
        "[/RUNTIME]"
    )


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def minify_context(context: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Lossless structural compaction; never ask another model to summarize context."""
    compact: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in context:
        value = dict(item)
        value.pop("type", None)
        value.pop("reason", None)
        if value.get("tool") == "get_data":
            value = {"d": value.get("source"), "q": value.get("query"), "r": value.get("result")}
        elif value.get("tool") == "execute":
            value = {"x": value.get("operation"), "p": value.get("param"), "r": value.get("result")}
        key = repr(sorted(value.items(), key=lambda pair: pair[0]))
        if key not in seen:
            seen.add(key)
            compact.append(value)
    return compact


def _hook_before(hooks: tuple[Hook, ...], kind: str, payload: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(h.before(HookContext(kind, payload)) for h in hooks)


def _hook_after(hooks: tuple[Hook, ...], kind: str, payload: dict[str, Any], result: Any) -> Any:
    for hook in reversed(hooks):
        value = hook.after(HookContext(kind, payload), result)
        if value is not None:
            result = value
    return result


class TinyAgent:
    def __init__(self, model: Callable[[str, str, list[dict[str, Any]]], dict[str, Any]],
                 get_data: Callable[[str, str], Any], execute: Callable[[str, str], Any],
                 runtime: Runtime, controls: PreflightControls, max_iterations: int = 8,
                 hooks: tuple[Hook, ...] = (), events: EventSink | None = None,
                 system_prompt: str = "", model_system_prompt: str = "",
                 strings: dict[str, str] | None = None, minify_enabled: bool = True,
                 minify_interval_tokens: int = 4096) -> None:
        self.model, self.get_data, self.execute = model, get_data, execute
        self.runtime, self.controls = runtime, controls
        self.max_iterations, self.hooks = max_iterations, hooks
        self.events = events or NullEvents()
        self.system_prompt = system_prompt
        self.model_system_prompt = model_system_prompt
        self.strings = strings or {}
        self.minify_enabled = minify_enabled
        self.minify_interval_tokens = max(1, minify_interval_tokens)
        self._last_minify_tokens = 0

    def _event(self, name: str, **payload: Any) -> None:
        self.events.publish(name, payload)

    def _data(self, source: str, query: str) -> Any:
        payload = {"source": source, "query": query}
        self._event("ContextRequested", **payload)
        for decision in _hook_before(self.hooks, "get_data", payload):
            if decision is not None:
                self._event("ContextCacheHit", **payload)
                return payload.get("result", decision)
        result = self.get_data(source, query)
        result = _hook_after(self.hooks, "get_data", payload, result)
        self._event("ContextRetrieved", **payload)
        return result

    def _execute(self, operation: str, param: str) -> Any:
        payload = {"operation": operation, "param": param}
        self._event("ExecutionRequested", operation=operation)
        for decision in _hook_before(self.hooks, "execute", payload):
            if decision is False:
                self._event("ExecutionDenied", operation=operation)
                raise PermissionError(self.strings.get("execution_denied", "execution denied by hook"))
        result = self.execute(operation, param)
        result = _hook_after(self.hooks, "execute", payload, result)
        self._event("ExecutionCompleted", operation=operation)
        return result

    def _minify_if_needed(self, context: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.minify_enabled:
            return context
        tokens = estimate_tokens(repr(context))
        if tokens < self._last_minify_tokens + self.minify_interval_tokens:
            return context
        compact = minify_context(context)
        after = estimate_tokens(repr(compact))
        self._last_minify_tokens = after
        if compact != context:
            self._event("ContextMinified", before_tokens=tokens, after_tokens=after)
        return compact

    def run(self, request: str) -> str:
        self._event("AgentStarted")
        context: list[dict[str, Any]] = []
        for requirement in preflight(request, self.runtime, self.controls):
            context.append({"type": "tool_result", "tool": "get_data", "source": requirement.source.value,
                            "query": requirement.query, "result": self._data(requirement.source.value, requirement.query),
                            "reason": requirement.reason})
        if self.minify_enabled:
            before = estimate_tokens(repr(context))
            context = minify_context(context)
            self._last_minify_tokens = estimate_tokens(repr(context))
            self._event("ContextMinified", before_tokens=before, after_tokens=self._last_minify_tokens)
        system = "\n\n".join(x for x in (self.system_prompt, self.model_system_prompt, runtime_prompt(self.runtime)) if x)
        for _ in range(self.max_iterations):
            context = self._minify_if_needed(context)
            self._event("ModelRequested")
            response = self.model(system, request, context)
            self._event("ModelCompleted")
            if response.get("answer"):
                self._event("AgentCompleted")
                return str(response["answer"])
            if call := response.get("get_data"):
                result = self._data(call["source"], call["query"])
                context.append({"tool": "get_data", **call, "result": result})
                continue
            if call := response.get("execute"):
                result = self._execute(call["operation"], call["param"])
                context.append({"tool": "execute", **call, "result": result})
                continue
            self._event("AgentFailed")
            return self.strings.get("unable_capabilities", "Unable to complete with the available capabilities.")
        self._event("AgentFailed")
        return self.strings.get("unable_limit", "Unable to complete within the tool-call limit.")


def local_file(path: str, root: str = ".") -> str:
    target = (Path(root) / path).resolve()
    root_path = Path(root).resolve()
    if root_path not in target.parents and target != root_path:
        raise PermissionError("path outside working directory")
    return target.read_text(encoding="utf-8")
