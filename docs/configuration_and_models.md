# TinyAgent Configuration and Model Roles

TinyAgent requirements are model-neutral. Concrete model names, providers, inference engines, and hardware-specific settings are implementation choices selected through evaluation.

## Model roles

```text
decision-model
fast-capability
small-capability
medium-capability
strong-capability
specialist-capability
```

A model registry maps concrete implementations to these roles.

```text
candidate implementations
          |
          v
       benchmark
          |
          +-- quality
          +-- latency
          +-- throughput
          +-- memory
          +-- cost
          +-- tool reliability
          +-- decision calibration
          |
          v
     capability profile
          |
          v
       model role
```

Replacing a model must not require changes to TinyAgent functional logic.

## Configuration boundary

The functional core does not contain model names, provider URLs, sampling settings, cache TTLs, security destinations, or provider-specific flags.

Configuration supplies model-role bindings, decision types and thresholds, routing policy, guardrails, tool policy, cache policy, evaluation criteria, and NFR settings.

Runtime state remains host-supplied and authoritative.

## Decision-centric configuration

TinyAgent supports Choice decisions for finite categories, Score decisions for ordered difficulty/relevance/quality/risk/urgency/capability, Boolean decisions for gates, confidence/probability values, parallel independent decisions, and dependency-aware sequencing for dependent decisions.

## Routing policy

```text
request
 |
 +--> category
 +--> difficulty
 +--> privacy
 +--> web-needed
 +--> tool-needed
 +--> context size
 +--> confidence
       |
       v
   policy engine
       |
       v
 capability role
```

The policy engine selects capability roles rather than concrete model names.

## Nine decision-centric use cases

1. Model routing — minimum capable model role.
2. Guardrails — detect injection, abuse, sensitive data, and policy violations.
3. Tool-call gating — allow, confirm, or deny.
4. Inbox triage — high-volume classification.
5. Reranking — relevance scoring.
6. LLM evaluation — typed quality scoring.
7. Bulk labeling — batched dataset classification.
8. Real-time decisions — repeated low-latency control.
9. Confidence gates — act, confirm, escalate, or human review.

## Security

A strict no-egress privacy policy requires sensitive-data detection before any cloud-bound operation.

```text
input
 |
 v
local privacy/security
 |
 +-- sensitive --> local-only
 |
 `-- safe ------> normal routing
```

Tool execution is authorized by host policy, not model text.

## Cache

```text
stable prompt prefix
      |
reusable context
      |
retrieved data
      |
provider prefix/KV
      |
safe deterministic results
```

Provider/inference KV caching stays inside the model adapter.

## Evaluation

Before assigning a candidate to a role, measure representative task quality and operational characteristics rather than parameter count alone.

Track task success, routing accuracy, decision calibration, tool-call reliability, latency/TTFT, throughput, memory usage, context handling, local/cloud cost, and escalation rate.
