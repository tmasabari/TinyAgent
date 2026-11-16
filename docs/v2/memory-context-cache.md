# TinyAgent v2 Memory, Context and Cache Architecture

## 1. Separate three kinds of state

| State | Meaning | Owner |
|---|---|---|
| Session history | Durable conversation and model-visible facts | DSH session log |
| Agent memory | Reusable semantic, episodic, procedural or working knowledge | Optional TinyAgent memory service |
| Inference cache | Model weights, prefix/prompt cache, KV cache, expert cache and engine residency | Inference provider and scheduler |

These must not be collapsed into one “memory” abstraction. The DSH session log is the authoritative record for the conversation. Engine KV state is transient/provider-specific. Agent memory is an explicit retrieval product with provenance and retention rules.

## 2. Cache-first decision pipeline

```text
1. Stable system/policy/tool prefix
2. Reusable session context
3. Context/data cache
4. Retrieved file/web/domain material
5. Provider prefix/KV cache
6. New inference computation
```

Preserve stable prompt prefixes and put volatile request data later. Keep timestamps, request IDs and rapidly changing metadata out of the stable prefix where feasible.

Do not infer compute saved from a provider cache-hit percentage. Capture provider-specific token counts, timing and cache counters.

## 3. Context compaction

Preserve the existing TinyAgent structural minifier as a compatibility behaviour:

- It is deterministic and lossless with respect to retained query/result payloads.
- It removes duplicate records and shortens redundant structural metadata.
- It does not call another model.
- It must not destabilise the static system prompt prefix.
- Its approximate `characters / 4` token estimator is a trigger only, not a benchmark measurement.

Future tokenizer-aware triggers may be provider-specific, but should not alter minifier semantics without a separate compatibility test.

## 4. Memory provider progression

Start with the smallest useful persistent backend:

1. No persistent memory: use DSH session context and current POC semantics.
2. SQLite memory provider for typed records and metadata.
3. Optional vector retrieval adapter if measured retrieval workloads justify it.
4. Optional Hindsight adapter behind the same memory contract.

Hindsight is an integration option, not a required core dependency. The core memory contract should not depend on a particular memory product.

## 5. Memory record requirements

Every record should include:

- Stable record ID and schema version.
- Tenant/user/project/agent scope where applicable.
- Record type and content.
- Source/provenance references.
- Creation/update times.
- Retention classification and expiration policy.
- Confidence/quality metadata where relevant.
- Deletion and invalidation semantics.

Retrieval must return provenance and must not silently elevate an untrusted retrieved passage into system instructions.

## 6. Context assembly

Context policy selects the minimum useful material and preserves its provenance. It should:

- Prefer exact recent session facts when relevant.
- Reuse valid cached retrieval results.
- Enforce token/context budget.
- Separate trusted runtime facts from untrusted external content.
- Preserve original task acceptance criteria across delegation.
- Keep stable prompt sections deterministic.

Semantic summarisation is not the default. Add it only when benchmark results show structural compaction is insufficient and quality/recall tests can detect losses.

## 7. Cache invalidation

- Workspace/file writes invalidate only affected file/retrieval entries.
- Model/provider changes invalidate incompatible provider KV state.
- Prompt/template changes invalidate matching prefix cache identity.
- Permission/scope changes invalidate cached data that depended on old authority.
- Memory deletion must invalidate derived retrieval/context entries where applicable.

Cache keys must encode relevant model, provider, tenant/project scope and authorization context. Cross-scope cache leakage is a security defect.

## 8. Metrics

Record cache layer, hit/miss, bytes/tokens, timing, invalidation reason and source identity. Keep provider cache telemetry separate from application context/data cache telemetry.
