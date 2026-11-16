# TinyAgent v2 Architecture Overview

## 1. Vision

TinyAgent remains a decision-first, minimal agent capability: deterministic preflight, typed decisions, just-in-time information acquisition and controlled execution. Version 2 changes its deployment and extension model: the official DeepSeek Harness becomes the application host, while TinyAgent, TinyRouter and LocalAMDAI capabilities are composed through Cordis plugins.

The aim is customisability without building another general-purpose runtime.

## 2. Architecture principles

1. **Decision != Generation != Execution.** Keep fast decisions, generated content and side effects distinct.
2. **Deterministic first.** Use known runtime facts and rules before spending model compute.
3. **Minimum capable model.** Choose capabilities based on measured task suitability, not model size alone.
4. **Model-neutral contracts.** Functional code consumes roles and capabilities, not vendor names.
5. **Preserve original intent.** Specialist delegation must retain the immutable task contract.
6. **Cache first.** Reuse context and inference state before recomputing or retrieving.
7. **Host-enforced safety.** Model proposals never authorize their own actions.
8. **Plugin replaceability.** Providers, policies and application behaviour are independently composable.
9. **NFR isolation.** Security, audit, telemetry, budgets and health attach through services and events.
10. **KISS / YAGNI / DRY / POLA.** Avoid a plugin-per-function design or premature distributed infrastructure.

## 3. System map

```text
                         DSH WEB HOST
                              |
                       Cordis composition
                              |
             +----------------+----------------+
             |                |                |
        Intelligence       Knowledge        Governance
             |                |                |
        TinyRouter          Memory          Permission
        Planner             Retrieval       Approval
        TinyAgent           Context         Audit
        Specialists         Cache policy    Sandbox
        Verifier            Search          Telemetry
             |                |                |
             +----------------+----------------+
                              |
                       Model scheduler
                              |
                       DSH ctx.llm seam
                              |
              +---------------+---------------+
              |               |               |
            Strata         PolyStrata       llama.cpp
              |               |               |
              +---------------+---------------+
                              |
                        ROCm / HIP / CPU
                              |
                       RX 9070 / host RAM

                Separate optional training plane
                     PyTorch ROCm / Unsloth
```

DSH owns Web serving, session/agent lifecycle and the Cordis host. TinyAgent v2 contributes capabilities; it does not duplicate these platform foundations.

## 4. Planes

### 4.1 Host and composition plane

- DSH launcher and Web profile.
- Cordis plugin lifecycle, dependency resolution, scopes and event system.
- DSH session/event log and default agent loop.
- Profile and bundle composition.
- DSH UI and plugin management.

### 4.2 Intelligence plane

- TinyRouter routing policy.
- Deterministic preflight and typed decisions.
- Planner and task decomposition.
- TinyAgent-compatible bounded task loop.
- Specialist registry and specialist execution.
- Escalation and task verification.

### 4.3 Knowledge plane

- Session-derived history (owned by DSH).
- Optional working, episodic, semantic and procedural memory providers.
- Retrieval/search providers.
- Context selection and structural compaction.
- Data cache, retrieval cache and context reuse policy.

### 4.4 Inference and resource plane

- Model registry and capability catalogue.
- Strata, PolyStrata and llama.cpp LLM adapters.
- Model loading/unloading and process lifecycle.
- ROCm/HIP device monitor.
- CPU/host RAM, VRAM and swap monitor.
- Admission control, model residency and request scheduling.

### 4.5 Execution and governance plane

- DSH tool registry and guarded execution pipeline.
- Filesystem, shell, browser, Git, HTTP and Docker providers.
- Sandbox and approval policies.
- Host-owned secrets, audit and permission controls.

### 4.6 Evaluation plane

- Deterministic verifiers.
- Inference, routing, planning and end-to-end benchmark suites.
- Reproducible run metadata and result storage.
- Resource and quality telemetry.

## 5. Request flow

```text
User request
   |
   v
DSH Session / Agent
   |
   v
Deterministic preflight + local privacy policy
   |
   +-- known / safe / deterministic --> direct capability
   |
   v
TinyRouter capability decision
   |
   v
Routing policy + resource admission
   |
   v
Planner (only when task decomposition is useful)
   |
   +--> specialist A --> observation --> verifier
   |
   +--> specialist B --> observation --> verifier
   |
   v
Final task verification
   |
   +-- failed --> bounded repair/escalation
   |
   v
DSH session settlement
```

The original task contract remains available across all specialist boundaries. A planner summary is additive and may not replace the user's original request or acceptance criteria.

## 6. Plugin granularity

A plugin represents an independently variable capability, provider, policy, or application contribution. Related plugins may be distributed together in one bundle. A trivial helper function does not need its own package.

The Cordis runtime kernel and DSH host remain foundational. The “everything is a plugin” objective applies to replaceable application capabilities, not to duplicating or decomposing the host runtime itself.

## 7. First target

The first milestone is intentionally narrow:

- DSH Web profile boots.
- TinyAgent and TinyRouter functionality is preserved.
- A request can be routed to one LocalAMDAI inference provider.
- Model admission is resource-aware.
- The original task and tool semantics remain valid.
- Benchmark evidence can be generated and compared with historical baselines.

Do not replace the default DSH agent loop in this first milestone.
