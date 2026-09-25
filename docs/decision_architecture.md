# TinyAgent Decision-Centric Architecture

This document captures the current decision-first router architecture, the nine decision-centric use cases, confidence gates, parallel decision evaluation, cache interaction, and model-neutral capability roles.

## Architecture

```text
USER REQUEST
     |
     v
L0 deterministic preflight/rules
     |
     v
DECISION PLANE
 Choice | Score | Boolean | confidence
     |
     v
POLICY PLANE
 thresholds | security | routing
     |
     v
EXECUTION PLANE
 model | tool | web
     |
     v
observe / verify / stop

Cross-cutting: cache | security | audit | metrics | tracing | budgets
```

## Nine primary use cases

1. Model routing — route to the minimum capable model role.
2. Guardrails — detect injection, abuse, sensitive data, and policy violations.
3. Tool-call gating — allow, confirm, or deny proposed tool calls.
4. Inbox triage — classify high-volume messages.
5. Reranking — score query/candidate relevance.
6. LLM evaluation — score model outputs against configurable criteria.
7. Bulk labeling — classify large datasets in batches.
8. Real-time decisions — support repeated low-latency decisions in loops.
9. Confidence gates — map confidence to act, confirm, escalate, or human review.

## Decision patterns

### Choice
Finite alternatives for categorization and lane selection.

### Score
Ordered values for capability, difficulty, risk, relevance, urgency, or quality.

### Boolean
Yes/no gates for privacy, web requirement, tool requirement, and policy conditions.

Every model-derived decision should expose confidence/probability when supported.

## Parallel decisions

```text
shared state
 |--- category ------\\
 |--- difficulty -----+--> policy
 |--- privacy --------/
 |--- web-needed ----/
```

Independent decisions can run in parallel when the inference backend supports it; dependent decisions remain ordered.

```text
A -> B -> C
```

## Confidence gate

```text
decision + confidence
          |
      +---+---+
      |       |
     high     low
      |       |
      v       v
    route   fallback / confirm / escalate / human
```

Confidence is a routing signal, not proof of semantic correctness; calibration and downstream outcome quality must be measured.

## Local privacy boundary

```text
user input
    |
    v
LOCAL privacy/security gate
    |
 +--+-----------------+
 |                    |
sensitive            safe
 |                    |
 v                    v
local-only        normal routing
                     |
              local / cloud / web
```

A strict no-egress guarantee requires the privacy decision itself to execute locally.

## Tool-call gate

```text
agent proposes tool call
          |
          v
    decision/security
          |
       +--+--+
       |  |  |
       v  v  v
     ALLOW ASK DENY
       |
       v
    execute
```

The host policy owns final authorization.

## Bulk decision processing

```text
huge dataset
    |
partition
 |  |  |  |
v  v  v  v
decision workers
 |  |  |  |
 +--+--+--+
     |
     v
labels / scores / ranks
```

This supports triage, labeling, reranking, and evaluation without requiring generated prose for every item.

## Model neutrality

Functional requirements use capability roles rather than model names:

```text
decision-model
fast-capability
small-capability
medium-capability
strong-capability
specialist-capability
```

Concrete implementations are selected through evaluation.

```text
candidate models
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
assigned role
```

## Cache interaction

```text
stable system/policy/tool prefix
              |
      reusable session context
              |
       current task/observation
              |
          decision
```

Keep stable content before volatile content to maximize reusable inference prefixes/KV state.

## System-1/System-2 pattern

```text
request
  |
  v
FAST DECISION LAYER
  |
  +-- confident --> cheap route
  |
  `-- uncertain --> stronger reasoning
```

The fast decision path should remain substantially cheaper/faster than the work it controls.

## Core invariant

> Use the smallest computation that can safely make the current decision; use generation only when generation is actually required.
