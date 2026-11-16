# TinyAgent v2 Routing, Planning and Compatibility

## 1. Preserve existing TinyAgent semantics

The current repository implements a compact Python agent with:

- `Runtime` facts: knowledge cutoff, current datetime, input modalities, OS, shell and working directory.
- Deterministic preflight into `file`, `web` and `domain` data requirements.
- A minimal two-tool surface: `get_data(source, query)` and `execute(operation, param)`.
- Hook callbacks around data acquisition and execution.
- An event sink for observable facts.
- Structural context minification that deliberately does not call another model.
- A bounded iteration loop.
- A simple local-file helper that constrains the resolved path to its root.

This implementation and its tests define the compatibility baseline. Version 2 must not silently change enum values, tool payload shapes, preflight semantics, context-minifier invariants or failure behaviour.

## 2. TinyRouter's responsibility

TinyRouter selects **which capability/model should handle a request**. It does not own the agent loop, task state, tool execution or verification.

Retain deterministic YAML routing as the first stage. Use a model-based classifier only where semantic classification adds value.

Recommended routing order:

1. Local privacy and security preflight.
2. Deterministic task/capability rules.
3. Check available model capability metadata.
4. Check resource admission.
5. Use TinyRouter model classification when rules cannot decide confidently.
6. Select a minimum capable route and a fallback.
7. Record reason codes and benchmark/trace identity.

A route recommendation can be refused by resource or security policy. The router is not an authorization component.

## 3. Capability-based routing

Do not encode functional logic as L1/L2/L3 model names. Preserve the original L1/L2/L3 policy as a compatibility mode, but make the long-term contract capability-based.

Example capability categories:

- `decision.classification`
- `reasoning.planning`
- `coding.edit`
- `terminal.command`
- `research.retrieval`
- `document.ocr`
- `math.solve`
- `verification.test`
- `verification.policy`

A model may advertise multiple capabilities, but every capability must be supported by evidence and evaluation. Model size or active parameter count alone does not establish long-horizon reliability.

## 4. Planner is not router

The planner is responsible for decomposition, dependency order, stop conditions and task state. It may use the selected model role but must not own provider-specific details.

Use a planner only when the task has dependencies or a meaningful multi-step execution horizon. For simple bounded actions, deterministic handling or direct capability routing is cheaper and safer.

Task plan requirements:

- Explicit subtask IDs and dependencies.
- Expected outputs and acceptance criteria.
- Allowed capabilities and forbidden actions.
- Bounded attempts and stop conditions.
- Original task contract reference.
- Verifier assignment.
- Escalation policy.

## 5. TinyAgent task contract and specialist handoff

Every delegated specialist must receive the immutable original request/acceptance contract or a reference resolvable by the trusted host. A compressed brief is never the sole representation of the user's intent.

Specialist output includes:

- Task ID and assignment ID.
- Result payload and output references.
- Actions taken and evidence.
- Warnings and unresolved assumptions.
- Verification status (not verified, passed, failed).
- Resource and execution trace references.

The planner may delegate but cannot assert success without the verifier's report.

## 6. Verifier-driven recovery

A failure should be classified before retry:

- Invalid format/schema.
- Missing acceptance criterion.
- Tool execution failure.
- Policy denial.
- Resource admission failure.
- Stale/unavailable data.
- Specialist capability mismatch.
- Planner/decomposition failure.

Use bounded recovery. Escalate model capability only when failure evidence supports it. A retry must not repeat an irreversible action without an idempotency/safety check.

## 7. DSH agent loop integration

Initial migration uses DSH's default Agent loop. TinyAgent becomes a set of services/tools/policies consumed by DSH's Agent and loop.

A future TinyAgent loop implementation is allowed only behind DSH's Agent interface and only after it passes lifecycle, cancellation, durable settlement, tool pipeline, retry, resume and session reconstruction tests.

## 8. Compatibility mapping

| Existing POC | v2 target |
|---|---|
| `Runtime` | Host-supplied, validated runtime facts |
| `PreflightControls` / `preflight()` | Deterministic preflight plugin |
| `Requirement` | Versioned retrieval request |
| `get_data` | DSH tool and/or provider service |
| `execute` | DSH tool through guarded execution |
| `Hook` | Cordis policy/interception plugin |
| `EventSink` | Cordis typed events; durable facts use DSH session events |
| `minify_context()` | Context policy plugin preserving lossless structural compaction |
| `TinyAgent.run()` | DSH Agent/loop integration, not duplicated in v2 |
| `local_file()` | DSH filesystem capability/sandbox provider |
| `tinyagent.yaml` | Profile/provider configuration and validated policy schemas |

## 9. Preserve the nine decision-centric use cases

The current architecture documents nine primitives: model routing, guardrails, tool-call gating, inbox triage, reranking, LLM evaluation, bulk labelling, real-time decisions and confidence gates. These remain valid capability families, but they should not all be implemented in the first migration.

Prioritize routing, privacy/tool gating and confidence fallback first. Add bulk decision and triage features only when a concrete workload justifies them.
