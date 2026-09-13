from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
import re
from typing import Callable, Any


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
class Requirement:
    source: Source
    query: str
    reason: str


CURRENT_WORDS = {
    "latest", "current", "today", "now", "recent", "recently",
    "newest", "updated", "currently", "this week", "this month",
}
FILE_RE = re.compile(r"(?:^|[\s\"'`(])((?:[\w.-]+/)*[\w.-]+\.(?:cs|fs|vb|js|ts|tsx|jsx|py|java|go|rs|cpp|c|h|json|yaml|yml|xml|sql|md|txt|csproj|sln|log))(?:$|[\s\"'`),])", re.I)
DATE_RE = re.compile(r"\b(20\d{2})(?:-(\d{1,2})(?:-(\d{1,2}))?)?\b")
DOMAIN_WORDS = {
    "github", "jira", "azure", "aws", "deployment", "production",
    "logs", "metrics", "monitoring", "ticket", "issue", "pull request",
    "branch", "commit", "resource group", "lambda", "ec2", "cloudwatch",
    "database", "database state", "environment",
}
STATE_WORDS = {
    "my", "our", "this", "status", "running", "deployed", "configured",
    "failed", "failure", "logs", "metrics", "production", "environment",
}


def _contains_any(text: str, values: set[str]) -> bool:
    text = text.lower()
    return any(v in text for v in values)


def _contains_post_cutoff_date(text: str, cutoff: datetime) -> bool:
    for match in DATE_RE.finditer(text):
        year = int(match.group(1))
        month = int(match.group(2) or 1)
        day = int(match.group(3) or 1)
        if datetime(year, month, day) > cutoff:
            return True
    return False


def preflight(request: str, runtime: Runtime) -> list[Requirement]:
    """Return mandatory context retrievals. Conservative by design."""
    requirements: list[Requirement] = []
    lower = request.lower()

    if _contains_any(lower, CURRENT_WORDS) or _contains_post_cutoff_date(request, runtime.knowledge_cutoff):
        requirements.append(Requirement(Source.WEB, request, "current_or_post_cutoff_information"))

    file_match = FILE_RE.search(request)
    if file_match:
        requirements.append(Requirement(Source.FILE, file_match.group(1), "local_artifact_reference"))
    elif _contains_any(lower, {"my code", "my project", "this file", "repository", "repo", "codebase", "local config", "local logs"}):
        requirements.append(Requirement(Source.FILE, request, "local_state_required"))

    if _contains_any(lower, DOMAIN_WORDS) and _contains_any(lower, STATE_WORDS):
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
    modalities = ",".join(runtime.input_modalities)
    return (
        "[RUNTIME]\n"
        f"knowledge_cutoff={runtime.knowledge_cutoff.isoformat()}\n"
        f"current_datetime={runtime.current_datetime.isoformat()}\n"
        f"input_modalities={modalities}\n"
        f"os={runtime.os}\n"
        f"shell={runtime.shell}\n"
        f"working_directory={runtime.working_directory}\n"
        "[/RUNTIME]"
    )


SYSTEM_PROMPT = """You are TinyAgent, a small efficient AI agent.

Goal: complete the user's task correctly with minimum reasoning, retrieval, actions, and output.

Rules:
- Treat runtime metadata as authoritative.
- Never invent knowledge, capabilities, tool results, or execution results.
- If required information is newer than the knowledge cutoff, retrieve it with get_data(web, ...); never answer from memory first.
- Retrieve local artifacts with get_data(file, ...) when they are required.
- Retrieve authoritative live/domain state with get_data(domain, ...) when required.
- Use execute only for necessary permitted actions.
- Verify important changes/results when practical.
- Apply KISS, YAGNI, DRY, and POLA.
- Prefer existing project conventions and standard libraries.
- Do not introduce unnecessary dependencies, abstractions, files, or features.
- Plan only enough to choose the next necessary action.
- Stop as soon as the task is complete.

Tool loop: understand -> retrieve if required -> act if required -> observe -> verify -> stop.
"""


class TinyAgent:
    def __init__(
        self,
        model: Callable[[str, str, list[dict[str, Any]]], dict[str, Any]],
        get_data: Callable[[str, str], Any],
        execute: Callable[[str, str], Any],
        runtime: Runtime,
        max_iterations: int = 8,
    ) -> None:
        self.model = model
        self.get_data = get_data
        self.execute = execute
        self.runtime = runtime
        self.max_iterations = max_iterations

    def run(self, request: str) -> str:
        context: list[dict[str, Any]] = []

        for requirement in preflight(request, self.runtime):
            context.append({
                "type": "tool_result",
                "tool": "get_data",
                "source": requirement.source.value,
                "query": requirement.query,
                "result": self.get_data(requirement.source.value, requirement.query),
                "reason": requirement.reason,
            })

        system = SYSTEM_PROMPT + "\n" + runtime_prompt(self.runtime)

        for _ in range(self.max_iterations):
            response = self.model(system, request, context)

            if response.get("answer"):
                return str(response["answer"])

            if call := response.get("get_data"):
                result = self.get_data(call["source"], call["query"])
                context.append({"type": "tool_result", "tool": "get_data", "source": call["source"], "query": call["query"], "result": result})
                continue

            if call := response.get("execute"):
                result = self.execute(call["operation"], call["param"])
                context.append({"type": "tool_result", "tool": "execute", "operation": call["operation"], "param": call["param"], "result": result})
                continue

            return "Unable to complete with the available capabilities."

        return "Unable to complete within the tool-call limit."


# Host adapters deliberately stay outside this module.
def local_file(path: str, root: str = ".") -> str:
    target = (Path(root) / path).resolve()
    root_path = Path(root).resolve()
    if root_path not in target.parents and target != root_path:
        raise PermissionError("path outside working directory")
    return target.read_text(encoding="utf-8")
