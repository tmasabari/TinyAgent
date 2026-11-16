# TinyAgent v2 Migration Plan

## 1. Strategy

Extend the official DeepSeek Harness host. Do not fork or patch DSH core initially. Preserve the existing Python TinyAgent implementation and test suite as the behavioural reference while migrating its capabilities into DSH plugins.

The migration is staged so that DSH Web hosting, existing TinyAgent functionality and LocalAMDAI inference can be validated independently.

## 2. Phases and exit criteria

### Phase 0 — Pin and validate DSH

- Clone the official `deepseek-ai/deepseek-harness` repository.
- Pin an exact commit and package manager/runtime toolchain.
- Build and launch the unmodified DSH `web` profile.
- Capture `dsh --profile web --dump-config`.
- Inspect service interfaces, profile patches, host/preset scopes and plugin lifecycle.
- Record a DSH compatibility matrix.

**Exit:** baseline Web profile boots; composition and extension APIs are documented.

### Phase 1 — TinyAgent v2 plugin foundation

- Create a separate plugin workspace/package boundary.
- Define versioned contracts and runtime schema validation.
- Create the base bundle and `tinyagent` profile.
- Add mount/unmount, dependency and configuration tests.
- Implement the TinyAgent bridge without changing POC behaviour.

**Exit:** custom profile boots and the foundation plugin can be unloaded cleanly.

### Phase 2 — Inference adapters and model resources

- Implement distinct Strata, PolyStrata and llama.cpp adapters.
- Bind each to DSH's actual `LlmAdapter` API.
- Add model registry and evidence-based capability metadata.
- Add ROCm monitor and resource admission.
- Add model lifecycle/readiness and cancellation.

**Exit:** provider switching is configuration-driven; scheduler prevents unsafe concurrent loads.

### Phase 3 — TinyRouter and TinyAgent integration

- Preserve deterministic preflight and YAML rules.
- Preserve legacy L1/L2/L3 mapping as compatibility mode.
- Implement capability-based route decisions.
- Integrate TinyAgent's two tools through DSH guarded tools.
- Preserve runtime facts and context minifier behaviour.
- Add immutable task contract support.

**Exit:** existing TinyAgent tests pass and DSH can execute the same task/tool patterns.

### Phase 4 — Verification and specialist workflow

- Add task planner and bounded specialist registry.
- Pass original task contract to every specialist.
- Add deterministic verifiers.
- Add bounded retry/escalation.
- Enforce sandbox and approval policies.

**Exit:** delegated workflows cannot report success without verification.

### Phase 5 — Memory, context and cache

- Start with session history plus existing structural compaction.
- Add SQLite memory provider only when a concrete memory use case is selected.
- Add optional vector/Hindsight adapters behind MemoryProvider.
- Add cache invalidation and context policy.
- Preserve provider-specific KV/prefix cache ownership.

**Exit:** session history, agent memory and inference cache are independent and testable.

### Phase 6 — Evaluation and optional training

- Add benchmark bundle and immutable fixtures.
- Run controlled routing/planning/specialist comparisons.
- Add ROCm training workflow only after resource isolation and adapter persistence checks.
- Consider alternative agent loop only if the DSH default loop cannot meet a demonstrated requirement.

**Exit:** architecture decisions are backed by reproducible task and resource measurements.

## 3. Rollback strategy

- Keep the current Python POC and its configuration as a reference implementation.
- Do not remove the POC until v2 compatibility tests pass.
- Keep DSH unmodified; disable the LocalAMDAI bundle/profile to return to the upstream host.
- Keep each inference provider optional and independent.
- Version profile/config changes and preserve known-good engine profiles.
- Never edit active engine configuration without a byte-identical backup and a documented rollback.

## 4. Implementation order

1. DSH pinned checkout and boot proof.
2. Contracts and TinyAgent bridge.
3. One inference adapter and resource monitor.
4. TinyRouter integration and compatibility tests.
5. Remaining inference adapters.
6. Verifier and specialist workflow.
7. Memory/cache extension.
8. Benchmark and training extensions.

This order deliberately validates the smallest vertical slice before expanding the plugin roster.
