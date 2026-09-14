from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import re
from urllib.request import Request, urlopen

from tinyagent import Runtime, TinyAgent
from tinyagent_config import load_config


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_data",
            "description": "Retrieve required information. source=file for local artifacts, web for current/public information, domain for authoritative live enterprise state. Return only the minimum useful data.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "enum": ["file", "web", "domain"]},
                    "query": {"type": "string", "description": "Specific, concise retrieval request."},
                },
                "required": ["source", "query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute",
            "description": "Perform one necessary permitted action. Use only when retrieval cannot complete the task.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["edit", "os", "web"]},
                    "param": {"type": "string", "description": "Exact action parameter."},
                },
                "required": ["operation", "param"],
                "additionalProperties": False,
            },
        },
    },
]

_TOOL_CALL_RE = re.compile(r"<tool_call>\s*(get_data|execute)\(\s*([\w-]+)\s*,\s*([\"'])(.*?)\3\s*\)\s*</tool_call>", re.S)


def parse_model_message(message: dict) -> dict:
    if tool_calls := message.get("tool_calls"):
        function = tool_calls[0].get("function", {})
        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            arguments = json.loads(arguments)
        if function.get("name") == "get_data":
            return {"get_data": arguments}
        if function.get("name") == "execute":
            return {"execute": arguments}

    content = message.get("content", "")
    try:
        value = json.loads(content)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    match = _TOOL_CALL_RE.search(content)
    if match:
        tool, first, param = match.group(1), match.group(2), match.group(4)
        return {tool: {"source" if tool == "get_data" else "operation": first,
                       "query" if tool == "get_data" else "param": param}}
    return {"answer": content}


def call_model(profile, system, request, context):
    body = {
        "model": profile.name,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps({"request": request, "context": context}, ensure_ascii=False)},
        ],
        "tools": TOOLS,
        "tool_choice": "auto",
        "parallel_tool_calls": False,
        "temperature": profile.temperature,
        "top_p": profile.top_p,
        "max_tokens": profile.max_tokens,
        "extra_body": {
            "top_k": profile.top_k,
            "chat_template_kwargs": {"enable_thinking": profile.thinking},
        },
    }
    req = Request(f"{profile.base_url.rstrip('/')}/chat/completions",
                  data=json.dumps(body).encode(),
                  headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=300) as response:
        payload = json.load(response)
    return parse_model_message(payload["choices"][0]["message"])


def main() -> None:
    parser = argparse.ArgumentParser(description="TinyAgent POC")
    parser.add_argument("request", nargs="+", help="user request")
    parser.add_argument("--config", default="config/tinyagent.yaml")
    parser.add_argument("--model", required=True, help="model profile from config")
    parser.add_argument("--cutoff", required=True, help="model knowledge cutoff, ISO date")
    args = parser.parse_args()

    config = load_config(args.config)
    profile = config.models[args.model]
    now = datetime.now(timezone.utc)
    cutoff = datetime.fromisoformat(args.cutoff).replace(tzinfo=timezone.utc)
    agent = TinyAgent(
        model=lambda system, request, context: call_model(profile, system, request, context),
        get_data=lambda source, query: {"source": source, "query": query, "status": "adapter-required"},
        execute=lambda operation, param: {"operation": operation, "param": param, "status": "adapter-required"},
        runtime=Runtime(knowledge_cutoff=cutoff, current_datetime=now),
        controls=config.preflight,
        max_iterations=config.max_iterations,
        system_prompt=config.system_prompt,
        model_system_prompt=profile.system_prompt,
        strings=config.strings,
        minify_enabled=config.minify_enabled,
        minify_interval_tokens=config.minify_interval_tokens,
    )
    print(agent.run(" ".join(args.request)))


if __name__ == "__main__":
    main()
