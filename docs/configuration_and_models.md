# TinyAgent Configuration and Initial Model Profiles

## Objective

TinyAgent is optimized for **task success per latency/token/compute** on small models.

Configuration is deliberately outside the functional core.

```text
YAML config
   |
   +--> agent behavior
   +--> preflight control words
   +--> model profiles
   +--> NFR defaults

runtime state remains host supplied
   |
   +--> current time
   +--> knowledge cutoff
   +--> OS / shell / cwd
   +--> modalities
```

## Configuration boundary

The core must not contain:

- preflight keyword lists;
- model names;
- sampling parameters;
- provider URLs;
- cache TTLs;
- security settings;
- audit destinations;
- provider-specific inference flags.

The core consumes typed configuration after loading/validation.

`config/tinyagent.yaml` is the POC source of truth.

## Command line

Model selection is explicit:

```powershell
python -m src.main --config config/tinyagent.yaml --model ling-3.0-tiny --cutoff 2026-01-01 "latest Python release"
```

```powershell
python -m src.main --config config/tinyagent.yaml --model ornith-1.5-9b --cutoff 2026-01-01 "fix src/AuthService.cs"
```

The cutoff is supplied by the host/operator rather than guessed by the model. This is important because deterministic freshness enforcement depends on it.

## Control words

All preflight control words live in YAML:

```yaml
preflight:
  current_words: [...]     # forces web retrieval
  file_phrases: [...]      # forces file retrieval
  domain_words: [...]      # candidate live-domain terms
  state_words: [...]       # makes domain retrieval state-specific
```

This keeps policy data separate from the algorithm.

## Model selection

### 1. Ling-3.0-tiny

Use `inclusionAI/Ling-3.0-tiny` as the first Ling benchmark.

It is a 7.9B-total-parameter hybrid-reasoning MoE with roughly 1.3B activated parameters/token and is explicitly intended for efficient agentic/local deployment. The current model guidance recommends thinking enabled with `temperature=1.0`, `top_p=0.95`, `top_k=20`. Current vLLM guidance also enables prefix caching and Ling-specific reasoning/tool parsers.

POC profile:

```yaml
ling-3.0-tiny:
  model: inclusionAI/Ling-3.0-tiny
  temperature: 1.0
  top_p: 0.95
  top_k: 20
  thinking: true
  prefix_cache: true
```

### 2. Ornith-1.5-9B

Use `ornith-ai/Ornith-1.5-9B` as the first Ornith benchmark.

It is the lightweight 9B dense Ornith-1.5 member. It supports reasoning, tool calling, a 256K context window and provider prefix caching. For precise coding, its current recommendation is `temperature=0.6`, `top_p=0.95`, `top_k=20`.

POC profile:

```yaml
ornith-1.5-9b:
  model: ornith-ai/Ornith-1.5-9B
  temperature: 0.6
  top_p: 0.95
  top_k: 20
  thinking: true
  prefix_cache: true
```

For a separate general-task experiment, use temperature 1.0 rather than mixing objectives in the coding benchmark.

## Why not larger variants first?

Do not start with Ling-3.0-flash or Ornith-1.5-35B-A3B.

- Ling-3.0-flash: 124B total, about 5.1B active/token.
- Ornith-1.5-35B-A3B: about 35B total, about 3B active/token.

They are useful later as stronger baselines. Starting with them would weaken the central TinyAgent hypothesis: **how far can a small model be pushed by better context acquisition and runtime support?**

## Inference/cache configuration

Prefix/KV caching is an inference-adapter concern, not core agent logic.

The initial profiles therefore express only the intent:

```yaml
prefix_cache: true
```

The actual provider/server configuration is owned by the inference deployment.

For Ling-3.0-tiny, the current vLLM recipe uses prefix caching and Ling tool/reasoning parsers.

For Ornith-1.5-9B, the current vLLM recipe uses prefix caching and Qwen-compatible tool/reasoning parsers.

## Separation rule

```text
Configuration
     |
     +--> chooses components
     +--> supplies tunable values
     +--> supplies policy data

Configuration does NOT:
     +--> execute tasks
     +--> implement preflight
     +--> implement cache
     +--> authorize actions
     +--> implement inference
```

That keeps the functional architecture stable while model/provider/NFR experiments change rapidly.

## Initial test matrix

| Test | Ling-3.0-tiny | Ornith-1.5-9B |
|---|---:|---:|
| static answer | yes | yes |
| current information | yes | yes |
| local file retrieval | yes | yes |
| domain retrieval | yes | yes |
| tool selection | yes | yes |
| edit + verify | yes | yes |
| application cache reuse | yes | yes |
| provider prefix/KV reuse | yes | yes |
| denied execution | yes | yes |

Measure success, hallucination, tool calls, input/output/cache tokens, TTFT, prefill/decode latency, end-to-end latency and cost.

The primary performance question is:

> **How much can deterministic context acquisition plus context/KV reuse improve a small model without sacrificing correctness or freshness?**
