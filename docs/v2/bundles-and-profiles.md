# TinyAgent v2 Bundles and Profiles

## 1. Composition strategy

Use the official DSH `web` profile as the host template. Add LocalAMDAI/TinyAgent bundles and a custom profile. Keep DSH's launcher, Web runtime, session services, agent lifecycle and Plugin Manager intact.

DSH bundle metadata uses a `dsh.bundle.patch` declaration in `package.json`. A profile declares ordered bundles in `dsh.profile`. Profile patches and home/CLI overlays have higher precedence than bundle rows. Check the pinned DSH documentation and package schemas before generating the actual package files.

## 2. Proposed bundles

| Bundle | Purpose | Example plugin families |
|---|---|---|
| `tinyagent-base` | Minimal contracts and host integration | TinyAgent service bridge, configuration, model catalogue |
| `tinyagent-intelligence` | Decision and task capabilities | TinyRouter, deterministic preflight, planner, specialists, verifier |
| `localamdai-inference` | AMD/local model integration | Strata, PolyStrata, llama.cpp, model scheduler |
| `tinyagent-memory` | Optional reusable memory | Memory core, SQLite provider, vector adapter, Hindsight adapter |
| `tinyagent-execution` | Execution capability providers | Filesystem, shell, Git, HTTP, browser, Docker, WASM |
| `tinyagent-governance` | Policy and controls | Privacy gate, tool policy, approval, sandbox, audit |
| `tinyagent-evaluation` | Benchmark and measurement | Routing tests, planner tests, verifier tests, inference benchmark |
| `localamdai-training` | Optional training workflows | ROCm PyTorch, Unsloth job provider, adapter validation |

Bundles group packages for distribution. They do not imply that every row in the bundle must be enabled in every profile.

## 3. Proposed initial profile

Profile ID: `tinyagent`  
Base: official DSH `web` profile composition  
Runtime: DSH Web UI

Intended composition:

```text
official dsh-base
      |
official dsh-web-app
      |
tinyagent-base
      |
tinyagent-intelligence
      |
localamdai-inference
      |
tinyagent-governance
      |
tinyagent-evaluation
      |
optional tinyagent-memory
      |
optional tinyagent-execution
      |
profile patch
      |
home patch / CLI overlay
```

The above is a composition intent, not copy-paste-ready DSH YAML. Exact bundle names, package IDs, row IDs and configuration shapes must be resolved from the pinned DSH checkout.

## 4. Agent presets

Presets select an agent's model defaults, prompt sections and visible tools. They must not contain shared host services that are consumed outside the agent scope.

| Preset | Purpose | Initial capabilities |
|---|---|---|
| `tinyagent-default` | Low-cost general assistant | TinyRouter, get_data, execute under policy, memory read |
| `tinyagent-coding` | Bounded coding tasks | Filesystem, Git, shell, tests, verifier |
| `tinyagent-research` | Current/public research | Search, browser, retrieval, citation verifier |
| `tinyagent-terminal` | Controlled system operations | Sandboxed terminal, approval, state verifier |
| `tinyagent-benchmark` | Fixed reproducible evaluation | Fixed model binding, benchmark tools, telemetry |
| `tinyagent-training` | Training-job orchestration | Dataset checks, isolated job submission, adapter validation |

The terminal preset must rely on host-level sandbox and permission providers; a model prompt alone is not a safety boundary.

## 5. Host versus preset ownership

A plugin/service belongs in the host plane when:

- A host-level DSH component consumes it.
- It must be unique across multiple agents.
- It tracks GPU/model process state shared by sessions.
- It owns global provider discovery, settings, telemetry or resource admission.

A plugin contribution may be agent/preset-scoped when:

- Only one agent needs its tools or prompt sections.
- It owns agent-local state.
- It does not provide a service required by a host component or other agents.

Before implementing a bundle, inspect injectors/consumers on both sides of the proposed scope. Avoid duplicate provider registrations and service invisibility.

## 6. Configuration layering

Recommended configuration domains:

- Provider endpoints and executable paths.
- Model catalogue and verified capabilities.
- Routing roles, thresholds and fallbacks.
- Resource reservations and admission limits.
- Prompt and context policy.
- Tool capability allowlists.
- Sandbox/approval policy.
- Cache TTL and invalidation.
- Benchmark fixture/version identity.

Secrets must use DSH credential facilities or a host-managed secret source. Do not commit API keys, tokens or private paths that are not intentionally portable.

## 7. Profile validation

Before accepting a profile:

1. Resolve every bundle package and patch file.
2. Validate all referenced plugin IDs and dependencies.
3. Dump the fully composed profile.
4. Check host/preset service visibility.
5. Boot the profile and inspect readiness.
6. Verify plugin unload/reload and resource cleanup.
7. Run the compatibility and benchmark smoke suites.

The exact configuration must be generated and checked against the selected DSH commit; do not assume patches are deep-merged.
