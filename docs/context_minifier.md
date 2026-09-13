# Context Minifier

Context size is a primary TinyAgent performance concern. The POC therefore performs deterministic, lossless structural compaction without calling another model.

## Configuration

```yaml
agent:
  context_minify:
    enabled: true
    interval_tokens: 4096
```

The interval is an approximate token threshold. Production benchmarking should replace the cheap `characters / 4` estimator with the actual model tokenizer.

## Behavior

1. Mandatory preflight results are minified once before the first model call.
2. After each context growth, the runtime estimates context tokens.
3. When another configured interval is reached, structural compaction runs.
4. Duplicate context records are removed.
5. Redundant structural fields are shortened/removed.
6. The actual result/query content is retained.
7. A `ContextMinified` event records before/after estimates.

```text
raw context
   |
   +-- remove duplicate records
   +-- remove redundant metadata
   +-- shorten structural keys
   |
   v
compact context
```

This is deliberately **not an LLM summarizer**. A summarizer would add latency, consume tokens and potentially lose facts. Add semantic summarization only if benchmarks prove structural compaction insufficient.

## Cache interaction

Minification must not destabilize the stable system prompt prefix. The system prompt remains outside dynamic context and model-specific prompts are fixed for a model profile.

```text
STATIC PREFIX
  base system prompt
  model-specific system prompt

DYNAMIC
  user request
  compacted context
  latest observation
```

This preserves the opportunity for provider prefix/KV caching while reducing the dynamic context payload.

## Important limitation

The current token estimator is provider-independent and intentionally cheap:

```text
estimated_tokens = ceil(characters / 4)
```

It is only a trigger, not a benchmark metric. Real token counts must come from the selected model tokenizer or provider response when measuring performance.
