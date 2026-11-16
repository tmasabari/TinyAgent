# TinyAgent v2 — Architecture and Design Documents

**Status:** Proposed architecture; documentation baseline only  
**Version:** 2.0  
**Host runtime:** DeepSeek Harness (DSH)  
**Composition:** Cordis plugins, bundles and profiles  
**Adoption strategy:** Extend the official DSH host; do not fork it initially  
**Runtime target:** DSH Web profile

## Purpose

TinyAgent v2 evolves the existing decision-first Python POC into a capability-oriented plugin ecosystem hosted by DeepSeek Harness. This is an architecture and migration specification. It does not claim that the v2 runtime has been implemented.

The existing Python implementation remains the behavioural compatibility baseline. Its current two-tool interface, deterministic preflight, typed decision concepts, context minification, hooks/events and cache-first intent must be preserved while the runtime integration is developed.

## Decisions

| Concern | Decision |
|---|---|
| Host | Official DeepSeek Harness |
| Composition | Cordis plugin lifecycle and services |
| Delivery | DSH bundles and a LocalAMDAI/TinyAgent profile |
| UI/runtime | DSH Web profile |
| Agent loop | Keep DSH default loop for initial migration |
| Routing | Preserve TinyRouter; evolve toward capability-aware routing |
| Agent | Preserve TinyAgent task/tool behaviour |
| Inference | Separate adapters for Strata, PolyStrata and llama.cpp |
| Hardware | AMD ROCm/HIP first; RX 9070 16 GB (gfx1201) |
| Memory | DSH session log remains conversation truth; separate optional agent memory |
| Cache | Engine-owned KV/prefix cache; context/data cache is a separate concern |
| Verification | Deterministic verifiers and explicit acceptance criteria |
| Training | Separate optional ROCm PyTorch/Unsloth capability plane |

## Documents

1. [Architecture overview](architecture-overview.md)
2. [DSH and Cordis source study](dsh-cordis-source-study.md)
3. [Plugin contracts](plugin-contracts.md)
4. [Bundles and profiles](bundles-and-profiles.md)
5. [Routing, planning and TinyAgent compatibility](routing-planning-tinyagent.md)
6. [Inference and AMD resource management](inference-and-resource-management.md)
7. [Memory, context and caching](memory-context-cache.md)
8. [Security and governance](security-governance.md)
9. [Benchmark and acceptance strategy](benchmark-acceptance.md)
10. [Migration plan](migration-plan.md)
11. [Decision records](decision-records.md)

## Non-goals for this documentation milestone

- Rewriting the Python POC.
- Replacing DSH's default agent loop.
- Implementing a second agent runtime.
- Claiming production-ready ROCm training.
- Assuming all model providers or engine features are interchangeable.
- Adding distributed caches, vector databases or complex multi-agent workflows before evidence justifies them.

## Source and evidence rules

Statements about the existing TinyAgent POC are based on the repository as inspected for this document set. Statements about DSH are based on the official source references in [DSH/Cordis source study](dsh-cordis-source-study.md). Hardware and benchmark statements are drawn from the LocalAMDAI project evidence cited in relevant documents.

Where an item is a design recommendation rather than an existing capability, it is labelled **Proposed**. Unknown or unverified engine support must remain unknown until tested against the active executable and model.
