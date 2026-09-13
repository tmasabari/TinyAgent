# TinyAgent

TinyAgent is a minimal agent runtime designed to make small language models more useful by giving them just-in-time access to missing knowledge, local state, and controlled actions.

The core idea is simple:

> **Do not make a tiny model know everything. Let it retrieve what it needs and act within explicit runtime limits.**

## Why

Small models are cheap and fast but have practical limits:

- knowledge cutoff can make current answers stale;
- model memory does not contain the user's files or repository state;
- the model may not know live enterprise/system state;
- the model may have limited input modalities;
- the model may not know the host OS, shell, working directory, or execution constraints.

TinyAgent addresses these with two tools only:

```text
get_data(source, query)
execute(operation, param)
```

## Architecture

```text
                     User request
                          |
                          v
                +--------------------+
                | Deterministic       |
                | preflight           |
                +----------+----------+
                           |
          +----------------+----------------+
          |                |                |
       post-cutoff     local artifact   live domain state
          |                |                |
         web              file            domain
          |                |                |
          +----------------+----------------+
                           |
                           v
                    Tiny language model
                           |
                   limited planning only
                           |
                    +------+------+
                    |             |
                 get_data      execute
                    |             |
                    +------+------+
                           |
                        observe
                           |
                      verify/done
```

### Deterministic preflight

The runtime should enforce rules that it can know without asking the model to reason about them.

Examples:

- information newer than `knowledge_cutoff` -> require `web` retrieval;
- explicit `latest`, `current`, `today`, `recent`, or a post-cutoff date -> require `web` retrieval;
- a referenced local path/file/repository artifact -> require `file` retrieval;
- live environment state such as deployment status, logs, metrics, tickets, or cloud resources -> require `domain` retrieval.

The model remains responsible for interpretation and synthesis, but stale-knowledge and environment-access decisions are not left entirely to the model.

## Runtime context

Inject a compact runtime block into the system prompt:

```text
[RUNTIME]
knowledge_cutoff=2025-06-01
current_datetime=2026-09-13T14:30:00+05:30
input_modalities=text
os=windows
shell=powershell
working_directory=C:\repo
[/RUNTIME]
```

These are authoritative runtime facts. The model must not claim capabilities that are not present.

## Tools

### `get_data`

```json
{
  "source": "file | web | domain",
  "query": "path | search query | domain query"
}
```

Use it when information is missing, uncertain, current, local, or authoritative external/domain state.

### `execute`

```json
{
  "operation": "edit | os | web",
  "param": "operation parameters"
}
```

Use it only when an external action is required. Execution must be policy-controlled and sandboxed by the host application.

## Minimal agent loop

```text
1. Run deterministic preflight.
2. Retrieve mandatory context.
3. Ask the tiny model for the next step.
4. Execute only the required tool call.
5. Feed the result back to the model.
6. Verify important changes.
7. Stop when complete.
```

Pseudo-code:

```text
context = preflight(user_request)

while not done and iterations < max_iterations:
    response = model(system_prompt, context, user_request)

    if response.answer:
        return response.answer

    if response.get_data:
        context += get_data(response.get_data)
        continue

    if response.execute:
        context += execute(response.execute)
        continue

    return "Unable to complete with available capabilities."
```

## Engineering principles

TinyAgent intentionally follows:

- **KISS** — keep the runtime simple;
- **YAGNI** — no planner, memory service, vector database, or multi-agent layer until evaluation proves a need;
- **DRY** — one generic data tool and one generic action tool;
- **POLA** — runtime behavior should be predictable and unsurprising.

Prefer standard libraries and small adapters. Avoid framework lock-in.

## Safety boundary

The model must never receive unrestricted host authority simply because `execute` exists.

The host should enforce:

- allowed paths;
- allowed commands;
- shell/OS compatibility;
- network access policy;
- destructive-action restrictions;
- timeouts and resource limits;
- audit logging.

The model proposes an action; the runtime decides whether the action is permitted.

## POC scope

This repository is a reference POC, not a production agent framework.

The first experiment should answer one question:

> **How much task-completion quality can a small model gain from deterministic context acquisition plus two tools, compared with the same model without tools and compared with routing directly to a larger model?**

Recommended evaluation groups:

| Case | Model | Tools | Purpose |
|---|---|---|---|
| A | Tiny | None | baseline |
| B | Tiny | `get_data` | knowledge/context gain |
| C | Tiny | both | tool-agent gain |
| D | Strong | None | quality baseline |
| E | Router | Tiny/Strong | cost/quality comparison |

## Non-goals for v0

Do not add these yet:

- multi-agent orchestration;
- long-term memory;
- vector database;
- separate planner/critic agents;
- large tool catalogs;
- workflow DSL;
- complex state machines.

Add complexity only when measurements show a real gap.
