# DeepSeek Harness + Cordis: Source-Based Architecture Study

**Inspected source snapshot:** `deepseek-ai/deepseek-harness` commit `39163dd30f703a79079e2d2446545cff3c453738`  
**Purpose:** Record the official DSH architecture used to design TinyAgent v2.  
**Caution:** DSH is developer-preview software; pin the exact revision during implementation and re-check all APIs against that checkout.

## 1. Source findings

### 1.1 Cordis is the composition framework

The official DSH architecture describes Cordis plugins as contributors of services, typed events and reversible effects to a shared context. Product components—including model adapter, tool registry, session log and agent loop—are composed as plugins.

The source describes no privileged application core that users are expected to patch. Extension is achieved by mounting plugins beside existing providers, with registrations/effects unwound when the owning plugin unloads.

**Design consequence:** TinyAgent v2 should mount new providers and policies instead of modifying DSH core packages.

### 1.2 Services and capability seams

DSH describes a capability seam through three roles:

- **Service Definition:** the contract/interface.
- **Service Provider:** an implementation of the contract.
- **Consumer:** a plugin using the service.

These roles may live in the same package, but the contract remains the dependency boundary.

**Design consequence:** TinyAgent should consume DSH service contracts, and LocalAMDAI engine implementations should adapt to those contracts. A planner must not import a concrete Strata client.

### 1.3 Core DSH service surfaces

The inspected architecture maps core services as follows:

| DSH service | Responsibility |
|---|---|
| `ctx.sessions` | Append-only SessionEvent log and in-memory store |
| `ctx.systemPrompt` | Prompt sections and tool-schema assembly |
| `ctx.tools` | Scoped tool registry and guarded execution pipeline |
| `ctx.agents` | Agent interface, live registry and agent events |
| `ctx.agentLoop` | Default Agent driver |
| `ctx.llm` | Message/stream vocabulary and LLM adapter seam |
| scope primitive | Per-agent scoped registrations |

The exact package/service map must be verified again on the pinned implementation revision.

### 1.4 Event domains

The inspected architecture distinguishes three event families:

1. **Session events:** durable facts appended to the session log and broadcast through `session/event`. Model-visible facts should be reconstructable from this log.
2. **Agent events:** live lifecycle and work events such as inbox, step, status, request, validation and continuation.
3. **Capability events:** provider/policy seams such as filesystem, tool and telemetry events.

Waterfall events require the listener to call `next()` to delegate. A listener that replaces a waterfall must intentionally short-circuit. Other serial events have different semantics; do not assume all event handlers are interchangeable.

**Design consequence:** use a session event for durable facts, agent events for in-flight observation/interception, and capability events for cross-cutting provider or policy integration.

### 1.5 Agent loop and Agent contract

The DSH source separates the Agent interface/live registry from the default agent-loop provider. The default loop is replaceable, but replacement affects step/turn state, cancellation, durable event settlement, tool execution and recovery.

**Design consequence:** keep the official default loop for the first migration. Any later alternative loop must implement the DSH Agent contract and pass the same lifecycle, cancellation, persistence and tool-pipeline tests.

### 1.6 Profiles and bundles

The architecture defines:

- A **bundle** as a distribution of Cordis configuration rows and plugin code.
- A **profile** as an ordered composition of bundles plus profile-level configuration/patches and optional out-of-tree plugins.

The inspected source describes layer order:

1. Profile's ordered bundles.
2. Profile `cordis.patch.yml`.
3. Harness home patch.
4. CLI `--patch` overlays.

A patch may replace an existing plugin row's complete config or insert new rows. It is not a deep field merge by default; replacement semantics must be respected.

The official documentation lists `web`, `headless`, `sdk`, `sdk-minimal` and `acp` profile templates. `dsh-base` is shared by Web, headless, SDK and ACP compositions; Web adds the browser application, while headless adds a one-shot runner without Web/HTTP/browser hosting.

**Design consequence:** use the official Web profile as the runtime base and add LocalAMDAI bundles/profile patches. Do not create a parallel executable or application boot tree.

### 1.7 LLM adapter seam

The inspected `packages/llm/llm/src/index.ts` defines the abstract `LlmAdapter` and the `ctx.llm` runtime. The adapter contract includes provider metadata, retry policy, model catalogue/resolution and streaming. `stream()` is the required provider operation. Adapter registrations are disposable and provider routes can be replaced atomically. The `llm/stream` waterfall is an interception point.

**Design consequence:** implement one DSH LLM adapter per inference project/runtime. Keep engine-specific configuration, process control and telemetry inside its adapter package.

### 1.8 Host plane versus agent/preset plane

The official composition examples distinguish host-level shared services from agent-preset contributions. A service consumed by a host component cannot be moved into a per-agent scope where that consumer cannot see it. A shared provider/registry that must be unique belongs in a shared plane; per-agent tool visibility and persona choices can be placed in presets.

**Design consequence:** before composing a plugin, map all service consumers. Do not put shared model registry, resource manager or cross-session services into per-agent presets merely because an agent uses them.

## 2. Extension map for TinyAgent v2

| TinyAgent v2 requirement | DSH seam or extension |
|---|---|
| Add Strata/PolyStrata/llama.cpp model route | `ctx.llm` adapter registration |
| Add model-facing TinyAgent tools | `ctx.tools` |
| Per-agent tool availability | Agent preset / scoped registration |
| Inject runtime/task context | Agent injection and prompt section facilities |
| Durable task facts | Session event extensions/projections |
| Route/observe a model call | `llm/stream` waterfall where appropriate |
| Add shell/filesystem backend | Existing shell/filesystem capability seams |
| Add sandbox | `ctx.sandbox` provider |
| Add telemetry | Telemetry service/events and provider |
| Add Web UI contribution | DSH client plugin/extension surface |
| Replace session persistence | DSH SessionPersistence contract (only if justified) |
| Replace agent loop | DSH Agent interface; defer until proven necessary |

## 3. Source snapshot files inspected

- `docs/architecture.md`
- `docs/capability-seams.md`
- `packages/llm/llm/src/index.ts`
- `docs/user/develop/practice/llm-adapter.md`
- `docs/user/develop/basic/publish.md`
- `packages/bundle/web-app/cordis.patch.yml`
- `packages/bundle/headless/cordis.patch.yml`
- Bundle package declarations in `packages/bundle/*/package.json`

## 4. Official references

- [DSH architecture at inspected commit](https://github.com/deepseek-ai/deepseek-harness/blob/39163dd30f703a79079e2d2446545cff3c453738/docs/architecture.md)
- [Capability seams](https://github.com/deepseek-ai/deepseek-harness/blob/39163dd30f703a79079e2d2446545cff3c453738/docs/capability-seams.md)
- [LLM adapter API](https://github.com/deepseek-ai/deepseek-harness/blob/39163dd30f703a79079e2d2446545cff3c453738/packages/llm/llm/src/index.ts)
- [LLM adapter development guide](https://github.com/deepseek-ai/deepseek-harness/blob/39163dd30f703a79079e2d2446545cff3c453738/docs/user/develop/practice/llm-adapter.md)
- [Bundle publishing guide](https://github.com/deepseek-ai/deepseek-harness/blob/39163dd30f703a79079e2d2446545cff3c453738/docs/user/develop/basic/publish.md)

## 5. Known limitations

This is a source review at a pinned commit, not a compatibility certification. DSH may evolve. Before writing plugins, check the current pinned checkout's exports, type declarations, package versions, profile schemas, event contracts and lifecycle tests. Do not copy example APIs from a newer or older branch without a version check.
