# TinyAgent

TinyAgent is a minimal, high-performance agent runtime designed to make small language models useful through just-in-time information acquisition, typed decisions, controlled actions, and aggressive reuse of context and inference state.

> **Do not make a tiny model know everything. Let it acquire what it needs, make small typed decisions, and act within explicit runtime limits.**

## Core design principles

1. **Decision != Generation != Execution.** Separate fast decisions from answer generation and tool execution.
2. **Deterministic first.** Use rules whenever the runtime already knows the answer.
3. **Minimum capable model.** Route to the smallest capability role that can safely perform the task and escalate only when evidence requires it.
4. **Model-neutral requirements.** Requirements name capability roles, never concrete model names or providers.
5. **Local-first security.** Sensitive-data decisions and authorization must remain inside the trusted host boundary when no-egress is required.
6. **Cache first.** Reuse context and inference state before retrieving or recomputing.
7. **NFR isolation.** Security, caching, audit, telemetry, budgets, and health are cross-cutting hooks/events/adapters.
8. **KISS + YAGNI + DRY + POLA.** Keep the functional core small and predictable.

## Architecture

```text
USER REQUEST
     |
     v
L0 deterministic preflight/rules
     |
     +--------------------+
     | obvious/known case |
     +---------+----------+
               | yes
               v
          direct route
               
               no
               |
               v
+---------------------------+
| DECISION PLANE            |
| Choice | Score | Boolean |
| confidence/probabilities  |
+-------------+-------------+
              |
              v
+---------------------------+
| POLICY PLANE              |
| routing | privacy | risk  |
| thresholds | budgets      |
+-------------+-------------+
              |
              v
+---------------------------+
| EXECUTION PLANE           |
| model roles | get_data    |
| execute | web/domain     |
+-------------+-------------+
              |
              v
        observe / verify
              |
              v
             DONE

--------- CROSS-CUTTING NFR PLANE ---------
security | cache | audit | metrics | tracing
health | resource budgets | persistence
```

See `docs/tinyagent_poc_context.md` and `docs/decision_architecture.md` for detailed context and diagrams.

## Nine decision-centric use cases

TinyAgent treats these as reusable decision primitives rather than separate frameworks:

1. **Model routing** — route requests to the minimum capable model role.
2. **Guardrails** — detect prompt injection, abuse, sensitive data, and policy violations before worker execution.
3. **Tool-call gating** — classify proposed actions as allow, confirm, or deny.
4. **Inbox triage** — classify large volumes of messages into configurable operational categories.
5. **Reranking** — score query/candidate relevance for deterministic ranking.
6. **LLM evaluation** — score model outputs using typed configurable criteria.
7. **Bulk labeling** — classify large datasets through batched/map-reduce-style decisions.
8. **Real-time decisions** — support repeated low-latency decisions in interactive loops.
9. **Confidence gates** — map confidence to act, confirm, escalate, or human review.

## Decision types

```text
Choice   -> finite alternatives
Score    -> ordered values
Boolean  -> binary gates
```

Independent decisions should run in parallel when the inference backend supports it; dependencies must remain ordered.

## Confidence is a control signal

```text
decision + confidence
          |
      +---+---+
      |       |
     high     low
      |       |
      v       v
    route   fallback / confirm / escalate / human
```

Confidence does not prove semantic correctness; calibration and downstream task outcomes must be measured.

## Local privacy boundary

```text
input
  |
  v
LOCAL privacy/security gate
  |
 +-- sensitive --> LOCAL ONLY
 |
 `-- safe ------> normal routing -> local / cloud / web
```

A strict no-egress design cannot rely on a cloud decision service for the privacy check because the input would already leave the trusted boundary.

## Tools

### `get_data`

```json
{"source":"file | web | domain","query":"string"}
```

### `execute`

```json
{"operation":"edit | os | web","param":"string"}
```

The model proposes actions; host policy authorizes them.

## Cache-first architecture

```text
stable prompt prefix
        |
reusable session/context
        |
retrieved data cache
        |
provider prefix/KV cache
        |
safe deterministic result cache
```

Provider-specific KV/prefix caching stays in the model/inference adapter rather than the functional core.

## Model capability roles

```text
decision-model
fast-capability
small-capability
medium-capability
strong-capability
specialist-capability
```

Concrete implementations are selected by evaluation using quality, latency, throughput, memory, cost, context handling, tool reliability, and decision calibration. A model replacement must not require functional-code changes.

## Configuration

Configuration externalizes routing policy, thresholds, model-role bindings, prompts, guardrails, tool policy, cache policy, evaluation criteria, and NFR settings. Runtime capabilities such as current time, cutoff date, OS, shell, working directory, and modalities remain host-supplied authoritative state.

## Minimal agent loop

```text
request
  -> deterministic preflight
  -> decision(s)
  -> policy
  -> get_data / execute
  -> observe
  -> verify when important
  -> stop
```

The model plans only enough to select the next necessary action.

## Performance

Measure decision latency, TTFT, prefill/decode latency, end-to-end latency, throughput, context reuse, KV cache hit rate, tool calls, escalation rate, task success, routing accuracy, calibration, local/cloud cost, and resource usage.

Keep context/prompt prefixes stable, send deltas instead of unchanged state, batch independent decisions, and compact context only when measurement shows it is necessary.

## Delivery stages

**POC:** prove typed decisions, deterministic preflight, routing, confidence fallback, configuration, logging, and benchmarking.

**MVP:** implement the nine decision-centric use cases plus privacy/security gates, tools, cache/context management, operational fallbacks, health checks, and metrics.

**BETA:** add parallel/dependency-aware decisions, evaluation-driven routing, model registry, adaptive thresholds, batch APIs, large-scale evaluation/labeling/reranking, and bounded autonomous loops.

**FINAL:** add durable/idempotent execution, resource budgets, policy versioning, trust boundaries, secret protection, multi-level caching, hardware-aware execution, continuous benchmarking, and automatic role replacement.

## Non-goals until measurements justify them

Avoid distributed caches, vector databases, long-term memory, multi-agent orchestration, large tool catalogs, workflow DSLs, and complex planner/critic layers until a measured requirement exists.
