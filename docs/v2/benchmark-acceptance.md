# TinyAgent v2 Benchmark and Acceptance Strategy

## 1. Evidence discipline

A result must record:

- Model ID, quantisation and model file hash.
- Engine/provider name, executable version, commit and configuration.
- Exact prompt/fixture, input/output token counts and output cap.
- Context occupancy and cache state.
- Requested and effective settings.
- TTFT, prompt-read/prefill time, decode rate and end-to-end latency.
- Peak/minimum VRAM, host available RAM, swap and resource pressure.
- Tool calls, retries, escalation and verifier outcomes.
- Output quality and acceptance checks.
- Run timestamp and hardware/software snapshot.

Do not compare different models, quantisations, engines/builds, prompts, output lengths, cache states, occupied contexts or settings as a controlled A/B. Use at least three repeats for new controlled comparisons and report median/range. Separate cold start, warm process, fresh prompt and reused-prefix runs.

## 2. Historical baselines to retain

The LocalAMDAI evidence pack contains these distinct records:

| Workload | Existing result | Evidence classification |
|---|---|---|
| Tiel / PolyStrata 32K short A/B | Whole KV decode 114.1, 124.4 tok/s; dynamic KV decode 112.0, 119.7, 122.6 tok/s | Controlled short-prompt records; telemetry completeness differs |
| Tiel / PolyStrata 131K fresh requests | 206 prompt tokens: 116.5 tok/s; 98,266 tokens: 59.6 tok/s; 130,268 tokens: 46.6 tok/s | Measured; targeted planted-needle recall passed at tested deep points |
| Qwen3.8-Flash-Next GSQ-RCO IQ1_M / PolyStrata 0.1.45 | Observational decode ~70.7–84.3 tok/s; captured 51,133-token request reused 49,942 tokens | Live observational telemetry, not controlled fresh prompt |
| Qwopus / llama.cpp HIP | Short smoke 46.8 tok/s decode; one interactive L0 record 47.81 tok/s | Separate workloads; not a matched A/B |
| ROCm/Unsloth QLoRA | One-step Qwen2.5-0.5B-Instruct QLoRA optimizer update passed, loss 1.8807, 668.9 MiB allocated | Compatibility smoke test, not throughput/convergence evidence |

These are historical, dated project records and must not be presented as current live measurements. Keep Strata and PolyStrata results distinct. Do not use the observational cache-hit values as proof of saved computation.

## 3. Required benchmark suites

| Suite | Measures |
|---|---|
| Inference | TTFT, prefill, decode, end-to-end, cold/warm startup |
| Cache/context | Fresh versus reused prompt, token reuse, context recall |
| Routing | Capability selection, routing accuracy, escalation rate |
| Planning | Requirement retention, decomposition validity, plan repair |
| Specialist | Bounded task success, handoff information loss |
| Verification | False acceptance, false rejection, defect detection |
| End-to-end | Task success, latency, tool calls, retries, cost/resources |
| Resource | Model load/unload, peak/minimum VRAM, RAM, swap, concurrency |
| Training | Optimizer steps, peak memory, adapter save/reload and inference |

## 4. Routing architecture comparisons

Compare with identical fixtures and controlled configuration:

1. Direct execution on the strongest suitable model.
2. Existing deterministic TinyRouter.
3. Existing L1/L2/L3 compatibility route.
4. Capability-aware TinyRouter with verifier.
5. Strong planner plus one bounded specialist.
6. Strong planner plus sequential specialists.
7. Planner with memory/context retrieval and verifier.

Record model-switch cost and model residency. A multi-model design must be evaluated on end-to-end task success and time, not only individual model speed.

## 5. Acceptance gates

### Compatibility
- Existing Python tests pass unchanged.
- Two-tool schema and enum values remain stable.
- Preflight source selection remains equivalent on fixtures.
- Context minifier remains deterministic and lossless under its stated invariants.
- Hook denial and event observation semantics remain test-covered.

### DSH integration
- DSH Web profile boots using pinned official runtime.
- LocalAMDAI profile composes through bundles and Cordis.
- TinyAgent service/tool registration is scoped correctly.
- Plugin unload releases all registrations/listeners/processes.
- Existing DSH session log remains authoritative.

### Inference and resources
- Each provider reports accurate executable/version/model identity.
- Unsupported options are rejected or explicitly recorded as unsupported.
- Resource admission prevents unsafe model starts.
- RX 9070 `gfx1201` is selected explicitly; integrated `gfx1036` is not assumed usable.
- Inference and training resource contention is controlled.

### Reliability and safety
- Original task contract survives specialist delegation.
- A verifier must pass before task completion.
- Sandbox and policy block forbidden actions independently of model output.
- Retries are bounded and do not repeat unsafe side effects.

### Performance
- No regression is claimed without matched benchmark evidence.
- Cache changes are measured separately from model/engine changes.
- Report medians/ranges, memory minima and output correctness.
