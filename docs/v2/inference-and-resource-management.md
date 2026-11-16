# TinyAgent v2 Inference and AMD Resource Management

## 1. Provider separation

LocalAMDAI records three distinct inference implementations:

- **Strata**: `Niko1221/Strata`, primarily associated in the supplied project registry with the Qwen GSQ-RCO model path.
- **PolyStrata**: `VecSzn/PolyStrata`, a distinct project with its own engines/binaries and model-specific option sets.
- **llama.cpp**: `ggml-org/llama.cpp`, the GGUF inference/runtime path.

Do not conflate these implementations. Do not assume CLI flags, KV formats, model formats, version numbers, server API details or speculative-decoding options transfer between them.

Implement one DSH LLM adapter per provider/runtime. A provider adapter is responsible for model discovery, exact-model metadata, streaming, cancellation, health, process lifecycle and provider telemetry.

## 2. Model catalogue and evidence

Each model record should declare:

- Stable model identity and provider identity.
- Model format, architecture and quantisation.
- Context metadata and modality support.
- Task capability tags.
- Tool/structured-output support.
- Speculative/MTP support where verified.
- Estimated VRAM/RAM requirements.
- Evidence status and source/version reference.

Use evidence labels consistently:

- **Measured:** observed in a captured controlled test.
- **Verified:** inspected in the live process, endpoint, executable or configuration.
- **Configured:** a setting was requested, but execution was not proved.
- **Estimated:** derived from an estimate/calculation.
- **Unknown/Unverified:** not established; do not present as supported.

A model's metadata context limit is not proof that every requested context size works in the selected engine.

## 3. ROCm-first resource policy

Target the discrete RX 9070, `gfx1201`, as the primary GPU. Do not infer that the integrated Radeon `gfx1036` is suitable because it is visible to ROCm. The supplied ROCm/Unsloth runbook records an earlier integrated-GPU matrix-multiplication failure.

Resource admission should inspect:

- GPU UUID/PCI identity and architecture.
- Total/free VRAM.
- Host total/available RAM and swap activity.
- Running inference/training processes.
- Model weights, draft layer, KV cache and expert cache estimates.
- Engine-specific load requirements and health state.

Before a heavyweight load, reserve memory conservatively. If the provider cannot estimate memory, require a controlled admission policy or explicit operator override.

## 4. Model residency and scheduling

The default assumption for the initial RX 9070 target is **one heavyweight GPU model workload at a time**. This is a conservative scheduling policy based on the supplied observations of very small VRAM headroom under some Strata/PolyStrata contexts. It is not a universal hardware limitation.

The scheduler should:

1. Reuse a ready model if it meets the requested capability.
2. Avoid loading a second heavyweight model while resource headroom is unsafe.
3. Queue/defer competing work or select an evaluated CPU/offload alternative.
4. Unload only idle models whose provider lifecycle is known and whose sessions are settled.
5. Retain model/context identity for cache reuse where valid.
6. Prevent training and inference from competing for the same GPU unless an explicit tested policy permits it.

Model switching is not free. Benchmark load/unload time, SSD reads, warmup, cache loss and end-to-end latency.

## 5. Engine-specific configuration isolation

The configuration model must not expose one global bag of flags applied to every engine.

Use provider-specific configuration schemas, for example:

- `providers.strata`
- `providers.polystrata`
- `providers.llama_cpp`

Validate each schema against the active executable and version before launch. Persist the requested arguments and the effective runtime-reported configuration separately.

A successful process start does not prove an option was accepted or used.

## 6. Training is a separate plane

The supplied runbook records a native ROCm PyTorch/Unsloth environment on RX 9070. It verifies a PyTorch optimizer-update smoke test and a one-step Unsloth QLoRA test on Qwen2.5-0.5B-Instruct. It explicitly leaves multi-step training, adapter save/reload, TRL SFTTrainer and larger-model scaling unverified.

The training plugin must:
- Use the existing isolated environment(s), not modify them during inference integration.
- Run a preflight compatibility check.
- Use resource admission before GPU allocation.
- Track package, ROCm/HIP, model and dataset versions.
- Verify adapter persistence and reload separately from training loss.
- Keep training throughput and convergence claims separate.

Do not expose training as a general model-facing tool in the default interactive profile. Make it an optional operator-controlled workflow.

## 7. Local machine evidence snapshot

The project notes inspected for v2 record:

| Item | Recorded value |
|---|---|
| CPU | AMD Ryzen 7 9700X, 8C/16T |
| RAM | 64 GB DDR5 |
| Discrete GPU | Gigabyte Radeon RX 9070 GAMING OC, 16 GB |
| GPU target | `gfx1201` |
| ROCm | `/opt/rocm/core-10.1` |
| HIP | `7.16.26385` |
| OS | Ubuntu 26.04.1 LTS |
| PyTorch | `2.14.0+rocm10.1.0` in recorded setup |

These are dated project observations, not a live host inventory. Revalidate before implementation or execution.

## 8. References

- [Strata](https://github.com/Niko1221/Strata)
- [PolyStrata](https://github.com/VecSzn/PolyStrata)
- [llama.cpp](https://github.com/ggml-org/llama.cpp)
- [ROCm documentation](https://rocm.docs.amd.com/)
- [ROCm PyTorch](https://github.com/ROCm/pytorch)
- [Unsloth AMD guide](https://unsloth.ai/docs/basics/amd)
