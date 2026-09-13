# TinyAgent POC Context

## 1. Problem

Small language models are attractive because of low latency, low infrastructure cost, and local/private deployment. Their usefulness is limited by stale knowledge, missing local/domain state, modality limits and unknown runtime constraints.

TinyAgent tests whether these limitations can be compensated with deterministic JIT retrieval and two tools while keeping the functional runtime extremely small.

## 2. Primary non-functional requirement: performance

**Performance is a first-class design constraint, not an optimization added later.**

The agent should avoid recomputing anything that can safely be reused. Application/context caching and inference/KV caching are different layers and must not be conflated.

```text
Request
  |
  v
Preflight -> cached context -> stable prompt prefix -> prefix/KV cache -> tiny model
                  ^                                      |
                  |                                      v
             data cache <--------- tools <--------- observations
```

Targets:

- minimize time-to-first-token (TTFT);
- minimize prefill work and repeated input tokens;
- minimize retrieval latency and duplicate retrievals;
- minimize tool calls and output tokens;
- maximize context reuse and provider KV/prefix-cache hits;
- preserve task success while doing so.

## 3. Functional architecture

The core remains deliberately small:

```text
request
  -> deterministic preflight
  -> mandatory context
  -> tiny model
  -> get_data / execute
  -> observation
  -> verify
  -> done
```

Core responsibilities are only interpretation, retrieval/action selection, observation and completion.

## 4. Cross-cutting NFR architecture

Cache, security, audit, telemetry, tracing, rate limits and cost controls must be completely separated from the functional architecture.

### Rule

> NFRs may observe, accelerate, decorate or constrain the functional pipeline, but the core must not depend on their implementations.

Use two small extension mechanisms:

```text
HOOK  = intercept / allow / deny / replace
EVENT = observe / record
```

Examples:

| NFR | Mechanism | Why |
|---|---|---|
| Data cache | `before/after` hook | hit can bypass the data adapter |
| Security | `before` hook | can deny execution |
| Audit | event sink | observes without changing behavior |
| Metrics | event sink | measures without core logic |
| Tracing | event sink | correlation without core dependency |
| Provider KV cache | model adapter | provider/inference-engine concern |
| Rate limit | host hook | policy before expensive work |

The core should know only tiny ports/interfaces, never Redis, OpenTelemetry, provider SDKs, databases or security products.

### Desired property

```text
NFR OFF  -> same functional behavior
NFR ON   -> same functional behavior + acceleration/controls/observability
```

If disabling an NFR requires changing the agent algorithm, the separation is wrong.

## 5. Tiny ports

Keep interfaces intentionally small:

```python
class Model:
    def generate(self, ...): ...

class DataTool:
    def get(self, source, query): ...

class Executor:
    def execute(self, operation, param): ...

class Hook:
    def before(self, event): ...
    def after(self, event, result): ...

class EventSink:
    def publish(self, name, payload): ...
```

The POC uses callable adapters for model/data/execution and exposes equivalent hook/event contracts in `src/tinyagent.py`.

## 6. Cache architecture

### L1: stable prompt cache

Keep stable system instructions and tool definitions deterministic and before volatile data. Do not place timestamps, request IDs or changing state before the cache boundary.

### L2: reusable context cache

Reuse stable project/session context where safe. Treat context as reusable objects rather than blindly replaying a growing transcript.

Conceptually:

```text
TASK
 |- FILE A
 |- FILE B
 |- WEB A
 `- TEST RESULT
       |
       v
    analysis
```

Each reusable item should have enough identity to detect changes: source, key/path, content/version hash and relevant generation.

### L3: retrieved data cache

`DataCacheHook` provides a small in-process TTL cache around `get_data`.

- file data: invalidate when content/mtime changes;
- web data: use short TTL according to freshness requirements;
- domain data: use TTL appropriate to the state being observed.

A cache hit must bypass the underlying data adapter. Cache miss calls the adapter and stores the result.

For multi-tenant use, the cache key must include all relevant security boundaries (tenant/user/project/model/policy context). The cache implementation owns key construction so the functional core remains unaware of identity infrastructure.

### L4: inference prefix/KV cache

The core does not implement provider KV caching. The model adapter should map the stable prefix to the capabilities of the selected inference engine/provider, such as provider prompt caching, vLLM automatic prefix caching or local runtime state.

Expose metrics where available:

```text
input_tokens
output_tokens
cache_read_tokens
cache_write_tokens
ttft_ms
prefill_ms
decode_ms
latency_ms
```

Do not fake a KV-cache abstraction inside TinyAgent. The adapter is the correct boundary.

### L5: safe action/result cache

Optional and later. Read-only deterministic operations may be cached. Mutations must invalidate affected context. Do not cache arbitrary side effects.

## 7. Cache invalidation

The safest POC rule is narrow invalidation:

```text
edit FILE A
   -> invalidate FILE A and dependent context
   -> retain unrelated FILE B / WEB A
```

A workspace generation/version can cheaply invalidate derived context after mutations without flushing everything. Add it only when evaluation demonstrates mutation-heavy workloads.

## 8. Context ordering for prefix/KV reuse

Use this conceptual order:

```text
STATIC
  system prompt
  tool definitions
  policies
  fixed capabilities

SESSION-STABLE
  project identity
  stable instructions
  reusable retrieved context

DYNAMIC
  current task
  current time
  latest observation
  current tool result
```

The exact provider API belongs to the model adapter. The important invariant is stable-before-changing.

## 9. Deterministic preflight

Preflight handles decisions that runtime information can establish reliably.

### MUST retrieve web

- latest/current/today/recent/updated requests;
- post-cutoff dates;
- current documentation/pricing/releases/vulnerabilities/availability;
- explicit source requests.

### MUST retrieve file

- explicit local paths/files;
- repository/codebase tasks;
- local config/logs/docs/test results required by the task.

### MUST retrieve domain

- deployment status;
- tickets/issues;
- cloud resources;
- production metrics/logs/monitoring;
- database/application state;
- connected repository state.

### MAY retrieve

Uncertain facts or supporting context when it materially improves correctness.

### DO NOT retrieve

Information already in context, stable knowledge the model can reliably provide, or unnecessary background.

The model must not answer from stale memory before mandatory web retrieval.

## 10. Runtime contract

The host supplies authoritative values:

```yaml
runtime:
  knowledge_cutoff: 2025-06-01
  current_datetime: 2026-09-13T14:30:00+05:30
  input_modalities: [text]
  os: windows
  shell: powershell
  working_directory: C:\repo
```

The model must never claim unsupported capabilities.

## 11. Tool contract

```yaml
get_data:
  source: file | web | domain
  query: string

execute:
  operation: edit | os | web
  param: string
```

The host owns authorization, sandboxing and resource limits.

## 12. Agent loop

```text
preflight
   |
mandatory retrieval
   |
context assembly
   |
model decision
   +---- get_data ----> observation --+
   |                                  |
   +---- execute -----> observation --+
                                      |
                                  next decision
                                      |
                                verify / done
```

The model plans only enough to choose the next useful action.

## 13. Events

Keep the event vocabulary small. Suggested events:

```text
AgentStarted
AgentCompleted
AgentFailed
ContextRequested
ContextCacheHit
ContextRetrieved
ModelRequested
ModelCompleted
ExecutionRequested
ExecutionDenied
ExecutionCompleted
```

Events should carry metadata, not duplicate large file/web/tool payloads. Store large artifacts separately if needed.

## 14. Security

Security is a pre-action hook, not a model instruction alone:

```text
model proposal
     |
     v
security/policy hook
   /       \
 deny     allow
            |
        sandboxed execute
```

Enforce path and command allowlists, network policy, OS compatibility, destructive-action restrictions, timeouts and resource limits in the host.

Cache isolation is also a security responsibility: never share sensitive cached data across incompatible security contexts.

## 15. Audit and telemetry

Audit and telemetry consume events. The core must not know where events are stored.

A local POC can use an in-memory recorder. Production can connect the same event port to a logging/tracing/metrics backend without modifying TinyAgent.

## 16. Evaluation

Benchmark at least:

- static knowledge;
- post-cutoff knowledge;
- local file tasks;
- multi-file tasks;
- live domain state;
- edit-and-test;
- unsupported modalities;
- denied/unsafe actions;
- repeated equivalent queries to measure cache reuse;
- repeated turns with a stable prompt prefix to measure provider KV/prefix reuse.

Measure:

```text
Task success
Accuracy / hallucination
Tool calls
Input / output tokens
Cache-read / cache-write tokens
Context reuse ratio
KV cache hit ratio
Fresh context ratio
TTFT
Prefill latency
Decode latency
End-to-end latency
Cost
Execution failures
Unnecessary retrieval
```

Definitions:

```text
Context Reuse Ratio = reused context tokens / total context tokens
KV Cache Hit Ratio  = cache-read tokens / total input tokens
Fresh Context Ratio = new context tokens / total context tokens
```

The performance goal is not "highest cache hit rate" in isolation. It is lower latency/token cost with unchanged or improved task success and freshness.

## 17. System prompt requirements

The system prompt should say:

1. you are a tiny efficient agent;
2. runtime metadata is authoritative;
3. never invent capabilities/results;
4. mandatory current/post-cutoff information must be retrieved before answering;
5. local/domain state must be retrieved when required;
6. use only the two tools;
7. execute only permitted necessary actions;
8. verify important changes;
9. use KISS/YAGNI/DRY/POLA;
10. prefer standard libraries and existing conventions;
11. plan minimally and stop when complete.

## 18. Explicit non-goals for v0

Do not add without measurements:

- Redis/distributed cache;
- vector DB;
- long-term memory;
- planner/critic agents;
- multi-agent orchestration;
- large tool catalog;
- workflow DSL;
- generic agent framework;
- provider-specific KV code in the core.

## 19. Relationship to TinyRouter

TinyRouter asks:

```text
Which model should handle this request?
```

TinyAgent asks:

```text
What does the tiny model need to acquire or do to solve it?
```

They can later compose so TinyAgent attempts the cheap path first and TinyRouter escalates only when required.
