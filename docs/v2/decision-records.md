# TinyAgent v2 Architecture Decision Records

## ADR-001: Extend official DeepSeek Harness

**Status:** Accepted  
**Decision:** Use the official DSH host and Cordis composition framework. Do not fork DSH initially.  
**Reason:** DSH already provides plugin lifecycle, service composition, session, agent and Web surfaces.  
**Consequence:** LocalAMDAI-specific behaviour is implemented as plugins, bundles and profile patches. DSH revision is pinned.

## ADR-002: DSH Web profile is the initial runtime

**Status:** Accepted  
**Decision:** Use the official Web profile as the application host.  
**Reason:** User selected DSH runtime and Web UI.  
**Consequence:** Do not introduce an independent application launcher or UI framework.

## ADR-003: Everything variable is a plugin; Cordis remains the kernel

**Status:** Accepted  
**Decision:** Make model providers, router, planner, memory, tools, verifier, policy, telemetry and UI contributions independently composable.  
**Reason:** Maximum customisation is required without duplicating runtime infrastructure.  
**Consequence:** Do not create one package per helper; preserve coherent bundle groupings and explicit service ownership.

## ADR-004: Preserve TinyAgent and TinyRouter behaviour

**Status:** Accepted  
**Decision:** Existing Python POC is the compatibility baseline.  
**Reason:** It contains deterministic preflight, two tools, hooks/events, context minifier and bounded iteration logic.  
**Consequence:** No silent changes to tool schemas or decision semantics. Use adapters during migration.

## ADR-005: Capability-aware routing with legacy compatibility

**Status:** Accepted  
**Decision:** Evolve routing from model tiers to task capability and evidence metadata, while retaining L1/L2/L3 YAML routing as a compatibility mode.  
**Reason:** Model identity and size are not reliable proxies for task suitability.  
**Consequence:** Capability registry and evaluation feed router policy; resource manager may reject a route.

## ADR-006: Planner, specialist and verifier are separate

**Status:** Accepted  
**Decision:** Separate route selection, task planning, specialist execution and verification.  
**Reason:** Weak planner decomposition and missing handoff context can reduce end-to-end quality.  
**Consequence:** Original task contract is immutable and available to delegated work; verification gates completion.

## ADR-007: Separate inference engines

**Status:** Accepted  
**Decision:** Strata, PolyStrata and llama.cpp get separate provider adapters.  
**Reason:** They are distinct projects with differing executable versions, flags and runtime behaviour.  
**Consequence:** No shared unvalidated CLI flag abstraction.

## ADR-008: ROCm-first with explicit resource admission

**Status:** Accepted  
**Decision:** Prioritise RX 9070 `gfx1201`, monitor VRAM/RAM and default to one heavyweight GPU workload at a time until concurrency is measured safe.  
**Reason:** Local evidence records very low free VRAM under some long-context configurations.  
**Consequence:** Model scheduler and process lifecycle are first-class. iGPU `gfx1036` is not assumed suitable.

## ADR-009: Session, agent memory and inference cache are separate

**Status:** Accepted  
**Decision:** DSH session log remains conversation source of truth; optional persistent memory and engine cache remain distinct.  
**Reason:** Different lifetimes, consistency and data semantics.  
**Consequence:** No duplicate chat-history database and no KV-as-long-term-memory design.

## ADR-010: Verifier-driven recovery

**Status:** Accepted  
**Decision:** Use deterministic verifiers and bounded evidence-based recovery.  
**Reason:** A model response or specialist completion does not prove task success.  
**Consequence:** Completion requires acceptance checks; retries must be bounded and safe.

## ADR-011: Training is optional and isolated

**Status:** Accepted  
**Decision:** ROCm PyTorch/Unsloth training is a separate optional plugin plane.  
**Reason:** Existing evidence is a smoke test, not full training validation.  
**Consequence:** Preserve Python environments and expose training only as an operator-controlled capability.

## ADR-012: Preserve historical benchmark evidence

**Status:** Accepted  
**Decision:** Existing records remain immutable; new comparisons use matched fixtures/configurations and explicit evidence classes.  
**Reason:** Avoid false performance conclusions.  
**Consequence:** Store model, quantisation, engine/build, prompt, cache, context, latency, memory and quality evidence for every run.
