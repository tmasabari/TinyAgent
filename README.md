# TinyAgent

TinyAgent is a minimal agent runtime designed to make small language models useful by giving them just-in-time access to missing knowledge, local state, and controlled actions.

> **Do not make a tiny model know everything. Let it retrieve what it needs and act within explicit runtime limits.**

## Design goals

1. **Correctness:** deterministic preflight prevents avoidable stale/context-free answers.
2. **Performance:** reuse context before recomputing it; maximize provider prefix/KV-cache reuse.
3. **Simplicity:** two tools, one small loop, standard library first.
4. **Isolation:** cache, security, audit, telemetry and other NFRs are cross-cutting adapters, not agent logic.

## Architecture

```text
                         User request
                              |
                              v
                     deterministic preflight
                              |
                    mandatory context retrieval
                              |
                  +-----------+-----------+
                  |       data cache       |  <-- hook
                  +-----------+-----------+
                              |
                              v
                     TinyAgent core
                              |
              +---------------+---------------+
              |                               |
           get_data                        execute
              |                               |
              +---------------+---------------+
                              |
                         observations
                              |
                              v
                         tiny model
                              |
                    provider/inference adapter
                              |
                       prefix / KV cache

       ---------------- cross-cutting NFR plane ----------------
       security hooks | audit events | telemetry | metrics | tracing
```

The core does **not** import or require cache, audit, security, telemetry, tracing, persistence, or a provider SDK.

### Hooks vs events

```text
Hook  = may this operation proceed / can it be served differently?
Event = what happened?
```

- **Cache:** hook around `get_data`; a hit bypasses the underlying data adapter.
- **Security:** hook before `execute`; denial stops the action.
- **Audit/telemetry:** event sink observes execution without changing the functional loop.
- **KV/prefix cache:** owned by the model/provider adapter because only that layer knows the inference engine.

NFRs can therefore be disabled without rewriting the agent.

## Cache hierarchy

Performance is a first-class requirement. TinyAgent separates application caching from inference caching:

```text
L1  stable prompt prefix       -> provider prompt/KV cache
L2  reusable context           -> context/data cache
L3  retrieved file/web/domain  -> DataCacheHook
L4  inference prefix/KV        -> model adapter / vLLM / llama.cpp / provider
L5  safe deterministic results -> optional execution adapter cache
```

The POC implements only the small in-process `DataCacheHook`. It does **not** pretend to implement provider KV caching; the model adapter should expose provider cache metrics such as cache-read tokens, cache-write tokens, TTFT and latency.

Keep stable prompt material before changing runtime/task data so provider prefix caches can reuse the longest possible prefix. Avoid timestamps, request IDs and other volatile values before the cache boundary.

For multi-tenant systems, cache keys must include the relevant security/tenant/project/model context. The cache adapter owns this concern; the core does not.

Writes should invalidate affected cached context. A simple workspace generation/version is preferable to broad cache flushing once mutation-heavy workloads are measured.

## Runtime context

The host injects authoritative capabilities:

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

The model must never claim unsupported capabilities.

## Two tools

### `get_data`

```json
{"source":"file | web | domain","query":"string"}
```

- `file`: local/project artifacts.
- `web`: public/current information.
- `domain`: authoritative live enterprise/runtime state.

### `execute`

```json
{"operation":"edit | os | web","param":"string"}
```

The model proposes an action. The host policy decides whether it is allowed.

## Deterministic preflight

Require `web` retrieval before model answering for:

- latest/current/today/recent/updated requests;
- dates after the knowledge cutoff;
- inherently current documentation, pricing, releases, vulnerabilities or availability.

Require `file` retrieval for required local artifacts and `domain` retrieval for required live state such as deployments, tickets, logs, metrics or cloud resources.

Do not retrieve information already present or unnecessary background.

## Minimal agent loop

```text
understand
   -> mandatory retrieve
   -> model chooses next action
   -> get_data / execute
   -> observe
   -> verify important results
   -> stop
```

The model plans only enough to choose the next necessary action.

## Performance rules

1. Preflight mandatory retrievals can run independently in parallel in an async host; do not add async complexity to the core until measured.
2. Cache semantic/data results separately from model KV/prefix caching.
3. Keep stable prompt prefixes deterministic.
4. Retrieve the smallest useful artifact.
5. Do not summarize small reusable context prematurely; summarization costs tokens and can lose detail.
6. Compact only when context size becomes a measured bottleneck.
7. Track cache-read tokens, input/output tokens, TTFT, latency, tool calls and task success.

Useful metrics:

```text
Context Reuse Ratio = reused context tokens / total context tokens
KV Cache Hit Ratio  = cache-read tokens / total input tokens
Fresh Context Ratio = new context tokens / total context tokens
```

## Security boundary

Execution parameters are untrusted model output. Host policy should enforce path/command/network allowlists, OS compatibility, destructive-action restrictions, timeouts and resource limits.

Security belongs in a hook because it can deny an operation. Audit belongs in events because it observes what happened.

## Engineering principles

- **KISS** — keep the functional runtime tiny.
- **YAGNI** — no speculative planner, memory service, vector DB or multi-agent layer.
- **DRY** — one generic data port and one action port.
- **POLA** — explicit capabilities and predictable behavior.

## POC evaluation

Compare:

| Case | Model | Tools | Purpose |
|---|---|---|---|
| A | Tiny | None | baseline |
| B | Tiny | `get_data` | context gain |
| C | Tiny | both | agent gain |
| D | Strong | None | quality baseline |
| E | Tiny | deterministic preflight | freshness gain |
| F | Tiny | cache + hooks/events | performance/NFR isolation |
| G | Router | Tiny/Strong | routing baseline |

Measure success, accuracy, hallucination, retrieval/tool calls, input/output/cache tokens, TTFT, end-to-end latency, cost, execution failures and unnecessary retrieval.

## Non-goals for v0

Do not add until measurements justify them:

- Redis or another distributed cache;
- vector database;
- long-term memory;
- planner/critic agents;
- multi-agent orchestration;
- large tool catalogs;
- workflow DSL;
- generic agent framework.

## TinyRouter relationship

TinyRouter asks:

```text
Which model should handle this request?
```

TinyAgent asks:

```text
What does a small model need to acquire or do to complete it?
```

A future composition can let TinyAgent try the cheap path first and escalate to TinyRouter only when the tiny path cannot solve the task.
