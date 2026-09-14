from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import re
from urllib.request import Request, urlopen

from .tinyagent import Runtime, TinyAgent
from .tinyagent_config import load_config


_TOOL_CALL_RE = re.compile(r"<tool_call>\s*(get_data|execute)\(\s*([\w-]+)\s*,\s*([\"'])(.*?)\3\s*\)\s*</tool_call>", re.S)


def parse_model_content(content: str) -> dict:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    match = _TOOL_CALL_RE.search(content)
    if match:
        tool, first, param = match.group(1), match.group(2), match.group(4)
        if tool == "get_data":
            return {"get_data": {"source": first, "query": param}}
        return {"execute": {"operation": first, "param": param}}
    return {"answer": content}


def call_model(profile, system, request, context):
    body = {
        "model": profile.name,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps({"request": request, "context": context}, ensure_ascii=False)},
        ],
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
    message = payload["choices"][0]["message"]
    content = message.get("content", "")
    return parse_model_content(content)


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
