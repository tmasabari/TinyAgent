# TinyAgent POC Context

## 1. Objective

Build a **minimal, high-performance agent runtime for tiny/weak language models**.

The runtime compensates for model limitations through deterministic just-in-time context acquisition and controlled actions:

- stale/missing knowledge -> web retrieval;
- missing local state -> file retrieval;
- missing live enterprise state -> domain retrieval;
- missing execution capability -> controlled action;
- unsupported capability -> explicit limitation/fallback.

### Primary objective

> **Maximize task success per unit of latency, tokens and compute while keeping the functional agent extremely small.**

Performance is a first-class constraint. Context reuse, prompt-prefix reuse and inference KV-cache reuse are architectural requirements, not later optimizations.

### Separation objective

The system has four independent concerns:

```text
                 +---------------------------+
                 | CONFIGURATION             |
                 | selects/composes behavior |
                 +-------------+-------------+
                               |
       +-----------------------+-----------------------+
       |                       |                       |
       v                       v                       v
+-------------+         +-------------+         +-------------+
| FUNCTIONAL  |         | NFR         |         | PROVIDER    |
| CORE        | hooks/  | cache       |         | inference   |
| preflight   | events  | security    |         | prompt/KV   |
| context     | <------ | audit       |         | caching     |
| model/tools |         | telemetry   |         |             |
+-------------+         +-------------+         +-------------+
```

**Configuration composes these parts; it does not become part of the agent algorithm.**

---

## 2. Architectural Rules

1. Functional core remains small and deterministic where possible.
2. NFRs are cross-cutting infrastructure and are isolated behind hooks/events/adapters.
3. Configuration is loaded and validated outside the functional core.
4. Provider-specific inference/cache behavior stays in model adapters.
5. Runtime state is supplied by the host and is distinct from configuration.
6. Disabling an NFR must not require changing the functional algorithm.
7. Prefer standard library and in-process mechanisms for the POC.
8. Do not add abstractions until measurement proves the need.

```text
KISS + YAGNI + DRY + POLA
          |
          v
small ports, small config, small core
```

---

## 3. Functional Architecture

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

The functional core owns only:

- request interpretation;
- deterministic preflight;
- context assembly;
- model invocation;
- tool selection;
- observation;
- completion/verification flow.

The core does **not** own:

- cache implementation;
- security policy implementation;
- audit persistence;
- telemetry/tracing backend;
- YAML/environment parsing;
- provider SDKs;
- provider-specific KV-cache logic.

---

## 4. Configuration Architecture

Configuration is its own layer.

```text
YAML / environment / host settings
                |
                v
        Config Loader/Validator
                |
       +--------+--------+
       |        |        |
       v        v        v
   Functional  NFR   Inference
      config  config   config
       |        |        |
       v        v        v
     Core    hooks/    model adapter
             events
```

### 4.1 Configuration responsibilities

The configuration layer should:

- load configuration;
- apply environment overrides where needed;
- validate values;
- separate functional, NFR and inference settings;
- construct/compose adapters and hooks.

It should **not** execute agent logic.

### 4.2 Functional configuration

Only settings required by the functional core belong here:

```yaml
agent:
  max_iterations: 8

model:
  name: tiny-model
```

The core receives typed/validated values. It should not know whether they came from YAML, environment variables or code.

### 4.3 Runtime configuration/state

Runtime facts are supplied by the host:

```yaml
runtime:
  knowledge_cutoff: 2025-06-01
  current_datetime: 2026-09-13T17:00:00+05:30
  input_modalities: [text]
  os: windows
  shell: powershell
  working_directory: C:\repo
```

Strictly speaking, this is **runtime state/capability context**, not application configuration. Keep the distinction because the model needs authoritative observed capabilities.

Current time should not unnecessarily precede stable prompt material because it reduces prefix-cache reuse.

### 4.4 NFR configuration

NFR settings are completely isolated:

```yaml
nfr:
  cache:
    enabled: true
    data_ttl_seconds: 300
  security:
    enabled: true
  audit:
    enabled: true
  telemetry:
    enabled: true
```

The functional core never reads `nfr.*`.

### 4.5 Inference configuration

Provider-specific settings belong to the inference adapter:

```yaml
inference:
  provider: vllm
  model: tiny-model
  prefix_cache: true
```

The core only sees the `Model` port. It must not contain `if provider == ...` logic.

### 4.6 Example complete POC configuration

```yaml
agent:
  max_iterations: 8

model:
  name: tiny-model

nfr:
  cache:
    enabled: true
    data_ttl_seconds: 300
  security:
    enabled: true
  audit:
    enabled: true
  telemetry:
    enabled: true

inference:
  provider: local
  prefix_cache: true
```

Runtime facts remain host-supplied rather than being copied into this static configuration.

### Configuration invariant

> **Configuration selects components and values; it never decides task-specific behavior.**

Do not build a configuration DSL. YAML plus a small loader/validator is enough for the POC.

---

## 5. Ports and Composition

Keep ports tiny:

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

Composition happens outside the core:

```text
config
  |
  +--> functional adapters
  +--> cache hooks
  +--> security hooks
  +--> audit/telemetry event sinks
  `--> model/provider adapter
                |
                `--> native prompt/KV cache
```

The current POC uses Python callables for the functional adapters and lightweight Protocol-compatible hook/event contracts.

---

## 6. Cross-Cutting NFR Architecture

NFRs may observe, accelerate, decorate or constrain the functional pipeline, but their implementations must remain outside the core.

```text
HOOK  = intercept / allow / deny / accelerate
EVENT = observe / record
```

| Concern | Mechanism | Responsibility |
|---|---|---|
| Data cache | hook | return reusable data before adapter call |
| Security | hook | deny unauthorized action |
| Rate limit | hook | reject expensive/forbidden work |
| Audit | event sink | record what happened |
| Metrics | event sink | measure latency/tokens/cache |
| Tracing | event sink | correlate operations |
| Provider KV cache | model adapter | reuse inference computation |

Desired behavior:

```text
NFR OFF -> functional path still works
NFR ON  -> same functional path + controls/acceleration/observation
```

---

## 7. Performance Architecture

Performance is optimized through multiple independent cache boundaries.

```text
L1  stable prompt/config prefix
L2  reusable session/context
L3  retrieved data
L4  provider prefix/KV
L5  safe deterministic results (later)
```

### L1 — prompt prefix reuse

Stable content must precede changing content:

```text
STATIC
  system prompt
  tool definitions
  fixed policies/capabilities

SESSION-STABLE
  project context
  stable instructions
  reusable retrieved context

DYNAMIC
  current task
  current time when needed
  latest observation
```

Do not place request IDs, timestamps or volatile state before stable content.

### L2 — context reuse

Represent reusable context as small identifiable items rather than blindly replaying a growing transcript.

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

Identity should include source/key and version/content hash where appropriate.

### L3 — data cache

The optional data-cache hook can cache `get_data` results.

Suggested identity/TTL:

```text
file   -> path + version/mtime/hash
web    -> normalized query + freshness policy + TTL
domain -> normalized query + security context + short TTL
```

Cache hits bypass the underlying adapter.

### L4 — provider prefix/KV cache

The functional core does not implement KV caching.

```text
TinyAgent -> Model port -> provider adapter
                         +--> prompt cache
                         +--> vLLM prefix/KV
                         +--> local inference cache
```

The adapter exposes cache metrics when supported:

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

### L5 — action/result cache

Later only. Cache safe, deterministic, read-only operations. Never blindly replay side effects.

---

## 8. Cache Invalidation

Prefer narrow invalidation:

```text
edit FILE A
   -> invalidate FILE A + dependent derived context
   -> retain unrelated cached context
```

A generation/version number may later simplify mutation-heavy invalidation. Do not add it until measurements justify it.

Cache isolation is also a security requirement. Sensitive keys must include the relevant tenant/user/project/security context.

---

## 9. Deterministic Preflight

Preflight makes decisions the runtime can establish reliably.

### MUST retrieve web

- latest/current/today/recent/updated requests;
- post-cutoff dates;
- current documentation/pricing/releases/vulnerabilities/availability;
- explicitly requested external sources.

### MUST retrieve file

- explicit local paths/files;
- repository/codebase tasks;
- local config/logs/docs/test results required by the task.

### MUST retrieve domain

- deployment state;
- tickets/issues;
- cloud resources;
- production metrics/logs/monitoring;
- database/application state;
- connected repository state.

### MAY retrieve

Uncertain facts or supporting context when materially useful.

### DO NOT retrieve

Information already in context, stable knowledge the model can reliably provide, or unnecessary background.

The model must never answer from stale memory before a mandatory retrieval.

---

## 10. Agent Loop

```text
request
  |
preflight
  |
mandatory retrieval
  |
context assembly
  |
model decision
  +---- get_data ----> observation --+
  |                                  |
  +---- execute -----> observation -+
                                      |
                                verify / done
```

The model plans only enough to select the next necessary action.

No cache lookup, security implementation, audit persistence, telemetry provider or configuration parsing is embedded in this loop.

---

## 11. Security Boundary

Security is a host-controlled pre-action hook.

```text
model proposal
      |
      v
security/policy hook
    /       \
  deny      allow
              |
         sandboxed host
```

Enforce:

- path/command allowlists;
- network policy;
- OS/shell compatibility;
- destructive-action restrictions;
- timeouts/resource limits;
- tenant/user/project isolation.

The model never receives unrestricted host authority.

---

## 12. Audit, Metrics and Telemetry

These consume events and must not become core dependencies.

Small event vocabulary:

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

Events should contain metadata, not duplicate large model/tool payloads.

---

## 13. System Prompt Requirements

The prompt should instruct the tiny model to:

1. treat runtime metadata as authoritative;
2. never invent capabilities/results;
3. retrieve mandatory current/post-cutoff information before answering;
4. retrieve local/domain state when required;
5. use only the two tools;
6. execute only necessary permitted actions;
7. verify important changes;
8. apply KISS/YAGNI/DRY/POLA;
9. prefer existing conventions and standard libraries;
10. plan minimally and stop when complete.

Deterministic runtime policy should enforce what the runtime already knows rather than spending model tokens rediscovering it.

---

## 14. Evaluation and Performance Gates

Compare:

```text
A Tiny/no tools
B Tiny + get_data
C Tiny + both tools
D Strong/no tools
E TinyAgent + preflight
F + data/context cache
G + provider KV/prefix cache
H + all NFRs
```

Measure:

```text
Task success
Accuracy / hallucination
Tool calls
Input/output tokens
Cache-read/write tokens
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

A cache optimization fails if it improves hit rate but harms freshness, correctness, security or overall latency.

---

## 15. Explicit Non-Goals for v0

Do not add without measurements:

- Redis/distributed cache;
- vector database;
- long-term memory;
- planner/critic agents;
- multi-agent orchestration;
- large tool catalog;
- workflow DSL;
- generic agent framework;
- provider-specific KV implementation in the functional core;
- configuration DSL;
- NFR logic embedded in the core.

YAML + a small configuration composition layer is sufficient.

---

## 16. Relationship to TinyRouter

TinyRouter asks:

```text
Which model should handle this request?
```

TinyAgent asks:

```text
What does the tiny model need to acquire or do to solve it?
```

Future composition:

```text
request
   |
TinyAgent
   |
   +--> solve cheaply with tiny model/tools
   |
   +--> cannot solve
            |
            v
       TinyRouter
            |
       stronger model
```

Escalation remains a fallback rather than the default solution to capability gaps.
