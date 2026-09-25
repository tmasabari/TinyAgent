# TinyAgent Context — Decision-First Architecture

## Purpose

TinyAgent is a minimal, high-performance agent runtime designed to make small language models useful through just-in-time information acquisition, typed decisions, controlled actions, and aggressive reuse of context and inference state.

> **Do not make a tiny model know everything. Let it acquire what it needs, make small typed decisions, and act within explicit runtime limits.**

## Core principles

- **Decision != Generation != Execution.**
- Use deterministic rules when the runtime already knows the answer.
- Use a tiny decision layer for fast, typed decisions rather than generated control JSON where possible.
- Use the minimum capable worker model and escalate only when evidence requires it.
- Keep model names, providers, and inference engines out of functional requirements.
- Select concrete model implementations through evaluation and configuration.
- Local-first processing is preferred when policy and capability permit it.
- Cache/reuse before recompute/retrieve.
- Keep NFRs outside the functional core.
- KISS, YAGNI, DRY, POLA.

## Architecture

```text
                         USER / CLIENT
                              |
                              v
                    +----------------------+
                    | L0 DETERMINISTIC     |
                    | PREFLIGHT / RULES    |
                    +----------+-----------+
                               |
                    obvious / safe cases?
                      +--------+--------+
                      |                 |
                     yes                no
                      |                 |
                      v                 v
                 route directly   +----------------------+
                                  | DECISION PLANE      |
                                  | Choice / Score /     |
                                  | Boolean + confidence |
                                  +----------+-----------+
                                             |
                         +-------------------+-------------------+
                         |                   |                   |
                         v                   v                   v
                      WHAT?              HOW HARD?           GATED?
                    category/task        capability          privacy/web/
                                                              tool/risk
                         |                   |                   |
                         +-------------------+-------------------+
                                             |
                                             v
                                  +----------------------+
                                  | POLICY / ROUTER      |
                                  | YAML + thresholds    |
                                  +----------+-----------+
                                             |
                       +---------------------+---------------------+
                       |                     |                     |
                       v                     v                     v
                  FAST LOCAL           SMALL/MEDIUM           STRONG/FRONTIER
                  CAPABILITY              CAPABILITY             CAPABILITY
                       |                     |                     |
                       +---------------------+---------------------+
                                             |
                                             v
                                  +----------------------+
                                  | TOOL / DATA PLANE    |
                                  | get_data / execute   |
                                  +----------+-----------+
                                             |
                                             v
                                       OBSERVE / VERIFY
                                             |
                                             v
                                           DONE

         -------------------- CROSS-CUTTING NFR PLANE --------------------
         security | cache | audit | metrics | tracing | budgets | health
```

## The nine primary decision-centric use cases

1. **Model routing** — route a request to the minimum capable model tier.
2. **Guardrails** — detect injection, abuse, sensitive information, and policy violations before worker execution.
3. **Tool-call gating** — allow, confirm, or deny proposed tool calls according to policy and confidence.
4. **Inbox triage** — classify large volumes of messages into configurable operational categories.
5. **Reranking** — score query/candidate relevance and rank deterministically.
6. **LLM evaluation** — score model outputs against configurable criteria using typed results.
7. **Bulk labeling** — classify large datasets with batched/map-reduce-style decisions.
8. **Real-time decisions** — support repeated low-latency decisions inside interactive loops.
9. **Confidence gates** — map confidence ranges to act, confirm, escalate, or human-review actions.

## Decision types

### Choice
Finite alternatives:

```text
request -> {chat, code, reasoning, image, ...}
```

### Score
Ordered capability/risk/relevance/etc.:

```text
0 ---- 2 ---- 4 ---- 6 ---- 8 ---- 10
```

### Boolean
Binary gates:

```text
private?     yes / no
web-needed?  yes / no
tool-needed? yes / no
```

Every model-derived decision should carry confidence/probability metadata.

## Confidence policy

```text
                 decision
                    |
              confidence?
          +---------+---------+
          |                   |
        HIGH                  LOW
          |                   |
          v                   v
     execute route       fallback / escalate
```

Confidence does not guarantee correctness; the system must distinguish low confidence from an incorrect high-confidence decision and measure calibration over time.

## Decision dependency model

Independent decisions should run in parallel:

```text
state
 |--- category ------ |--- difficulty -----+--> policy
 |--- privacy --------/
 |--- web-needed ----/
```

Dependent decisions must remain ordered:

```text
A -> B -> C
```

The runtime should explicitly represent decision dependencies rather than assuming every decision can be fused.

## Local-first security boundary

A privacy/security decision must occur before cloud routing whenever the request may contain sensitive information.

```text
USER
 |
 v
LOCAL SECURITY / PRIVACY GATE
 |                 |
private           safe
 |                 |
 v                 v
LOCAL ONLY       normal policy
                  |
                  v
             local / cloud / web
```

Cloud-based decision services cannot provide a strict "nothing leaves the machine" guarantee because the input must reach the service to be classified.

## Two-tool agent surface

### get_data

```json
{"source":"file | web | domain","query":"string"}
```

- `file`: local/project information.
- `web`: current/public information.
- `domain`: authoritative live application/enterprise state.

### execute

```json
{"operation":"edit | os | web","param":"string"}
```

The model proposes; host policy authorizes.

## Cache-first architecture

```text
L1 stable prompt prefix
       |
L2 session / reusable context
       |
L3 retrieved data cache
       |
L4 provider prefix / KV cache
       |
L5 safe deterministic result cache
```

Important invariant:

> **Never trade correctness, freshness, or security for a higher cache-hit ratio.**

Stable prompt material must precede volatile task state to maximize reusable provider prefixes.

## Context strategy

- Keep stable system/policy/tool definitions fixed.
- Represent reusable evidence as identifiable context items.
- Send context deltas instead of replaying unchanged state.
- Compact structurally before using another LLM to summarize.
- Use actual model tokenizers for benchmark measurements.
- Preserve required evidence while removing redundant metadata.
- Use checkpoints for long-running tasks.

## Agent lifecycle

```text
request
  |
  v
L0 preflight
  |
  v
decision(s)
  |
  v
policy
  |
  +--> get_data ----> observe
  |
  +--> execute -----> observe
  |
  v
verify
  |
  +--> continue if necessary
  |
  v
stop
```

## Model capability roles

Functional requirements refer to capability roles, not model names:

```text
decision-model
fast-capability
small-capability
medium-capability
strong-capability
specialist-capability
```

A model registry/evaluation system determines which concrete implementation currently fills each role.

## Evaluation-driven model replacement

```text
candidate models
      |
      v
task benchmark
      |
      +--> quality
      +--> latency
      +--> throughput
      +--> memory
      +--> cost
      +--> context handling
      +--> tool reliability
      +--> decision calibration
      |
      v
capability profile
      |
      v
MODEL ROLE
```

Replacing a model must not require changing TinyAgent functional logic.

## NFR separation

```text
                 FUNCTIONAL CORE
       preflight -> decide -> route -> act
                       |
                 hooks / events
                       |
       +---------------+--------------------+
       |               |                    |
    security         cache               telemetry
    audit            metrics             tracing
    budgets          health              persistence
```

- Hooks may accelerate, constrain, allow, or deny.
- Events observe what happened.
- Provider-specific KV/prefix caching belongs to the inference adapter.

## Performance metrics

At minimum measure:

```text
routing latency
decision latency
TTFT
prefill latency
decode latency
end-to-end latency
tokens/sec
cache hit ratio
context reuse ratio
fresh context ratio
tool-call count
escalation rate
task success
routing accuracy
confidence calibration
cloud/local cost
resource usage
```

Definitions:

```text
Context Reuse Ratio = reused context tokens / total context tokens
KV Cache Hit Ratio  = cache-read tokens / total input tokens
Fresh Context Ratio = new context tokens / total context tokens
```

## Iterative delivery stages

### POC
Prove typed decisions, deterministic preflight, routing, confidence fallback, configuration, logging, and benchmarking.

### MVP
Add the nine decision-centric use cases, privacy/security gates, tool authorization, cache-first execution, context management, health/fallbacks, and operational metrics.

### BETA
Add parallel independent decisions, dependency-aware decision execution, evaluation-driven routing, model registry, adaptive thresholds, batch APIs, reranking/labeling/evaluation pipelines, and bounded autonomous loops.

### FINAL
Add durable execution, idempotency, resource budgets, policy versioning, trust boundaries, secret protection, multi-level caching, hardware-aware execution, continuous benchmarking, and automatic capability-role replacement.

## Non-goals until evidence requires them

Do not introduce distributed caches, vector databases, long-term memory, multi-agent orchestration, large tool catalogs, workflow DSLs, or complex planner/critic layers without measurements showing a concrete need.

## Relationship with TinyRouter

TinyRouter is a specialized model-selection component.

TinyAgent is the broader decision-and-action runtime:

```text
TinyAgent
  |
  +--> solve cheaply
  |
  +--> need stronger capability
             |
             v
         TinyRouter
             |
             v
       selected capability
```

The composition should remain optional and model/provider agnostic.
