from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from urllib.request import Request, urlopen

from .tinyagent import Runtime, TinyAgent
from .tinyagent_config import load_config


def call_model(config, system, request, context):
    prompt = {
        "system": system,
        "request": request,
        "context": context,
        "response_format": {
            "answer": "string, or null",
            "get_data": {"source": "file|web|domain", "query": "string"},
            "execute": {"operation": "edit|os|web", "param": "string"},
        },
    }
    body = {
        "model": config.name,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "temperature": config.temperature,
        "top_p": config.top_p,
        "max_tokens": config.max_tokens,
    }
    if config.top_k:
        body["extra_body"] = {"top_k": config.top_k}
    body["extra_body"] = {
        **body.get("extra_body", {}),
        "chat_template_kwargs": {"enable_thinking": config.thinking},
    }
    req = Request(
        f"{config.base_url.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=300) as response:
        payload = json.load(response)
    content = payload["choices"][0]["message"].get("content", "")
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"answer": content}


def main() -> None:
    parser = argparse.ArgumentParser(description="TinyAgent POC")
    parser.add_argument("request", nargs="+", help="user request")
    parser.add_argument("--config", default="config/tinyagent.yaml")
    parser.add_argument("--model", required=True, help="model profile from config")
    parser.add_argument("--cutoff", required=True, help="model knowledge cutoff, ISO date")
    args = parser.parse_args()

    config = load_config(args.config)
    model = config.models[args.model]
    now = datetime.now(timezone.utc)
    cutoff = datetime.fromisoformat(args.cutoff).replace(tzinfo=timezone.utc)

    agent = TinyAgent(
        model=lambda system, request, context: call_model(model, system, request, context),
        get_data=lambda source, query: {"source": source, "query": query, "status": "adapter-required"},
        execute=lambda operation, param: {"operation": operation, "param": param, "status": "adapter-required"},
        runtime=Runtime(knowledge_cutoff=cutoff, current_datetime=now),
        controls=config.preflight,
        max_iterations=config.max_iterations,
    )
    print(agent.run(" ".join(args.request)))


if __name__ == "__main__":
    main()
