# TinyAgent v2 Plugin Contracts

**Status:** Proposed contracts. These are design-level interfaces, not existing DSH API declarations.

## 1. Contract rules

- The DSH host owns the Cordis context and service lifecycle.
- LocalAMDAI packages consume capabilities through contracts, never concrete provider imports.
- Every provider registration and listener must be owned by a plugin lifecycle and disposed on unload.
- All cross-plugin payloads require versioned, validated schemas.
- No secrets or unredacted sensitive request material should be written to generic telemetry.
- Service ownership and scope (host-wide versus agent-local) must be explicit.

## 2. Contract catalogue

| Contract | Owner/provider | Consumers |
|---|---|---|
| `ModelCatalog` | Model registry | Router, scheduler, UI |
| `InferenceProvider` | Engine adapter | DSH LLM adapter, scheduler |
| `RoutingPolicy` | TinyRouter/policy provider | Planner/agent |
| `ResourceManager` | ROCm/process monitor | Scheduler, adapters |
| `TaskContract` | Planner/task service | Specialists, verifier |
| `Planner` | Planner provider | Task orchestrator |
| `Specialist` | Specialist provider | Planner/task service |
| `Verifier` | Verification providers | Planner/task service |
| `MemoryProvider` | Memory backend | Memory service, context policy |
| `ContextPolicy` | Context manager | Agent prompt assembly |
| `CachePolicy` | Cache provider/policy | Retrieval, context and inference scheduler |
| `BenchmarkRunner` | Evaluation bundle | CI, manual benchmark command |
| `TrainingJobProvider` | Optional ROCm training integration | Training workflow |

## 3. Model catalogue

```ts
export interface ModelCapability {
  readonly providerId: string;
  readonly modelId: string;
  readonly taskCapabilities: readonly string[];
  readonly inputModalities: readonly string[];
  readonly outputModalities: readonly string[];
  readonly contextWindow?: number;
  readonly quantization?: string;
  readonly memory?: {
    readonly estimatedVramMiB?: number;
    readonly estimatedHostRamMiB?: number;
    readonly cpuOffload?: boolean;
    readonly kvStreaming?: boolean;
  };
  readonly features: {
    readonly toolCalling?: boolean;
    readonly structuredOutput?: boolean;
    readonly speculativeDecoding?: boolean;
    readonly mtp?: boolean;
  };
  readonly evidence: "verified" | "configured" | "unknown";
}
```

The evidence field prevents a configured option from being misrepresented as a verified feature. Catalogue values are capability metadata, not a substitute for testing.

## 4. Inference provider

```ts
export interface InferenceProvider {
  readonly id: string;
  listModels(signal?: AbortSignal): Promise<readonly ModelCapability[]>;
  inspect(modelId: string, signal?: AbortSignal): Promise<ModelCapability>;
  stream(
    request: InferenceRequest,
  ): AsyncIterable<InferenceChunk>;
  health(signal?: AbortSignal): Promise<ProviderHealth>;
  load?(modelId: string, options: LoadOptions, signal?: AbortSignal): Promise<void>;
  unload?(modelId: string, signal?: AbortSignal): Promise<void>;
}

export interface InferenceRequest {
  readonly requestId: string;
  readonly modelId: string;
  readonly messages: readonly ModelMessage[];
  readonly signal?: AbortSignal;
  readonly limits: {
    readonly maxOutputTokens?: number;
    readonly latencyClass: "interactive" | "normal" | "batch";
    readonly qualityClass: "fast" | "balanced" | "high";
  };
  readonly trace: {
    readonly taskId?: string;
    readonly agentId?: string;
    readonly benchmarkRunId?: string;
  };
}
```

DSH integration should adapt each LocalAMDAI provider to the actual pinned DSH `LlmAdapter` interface. The conceptual interface above is intentionally provider-neutral; it is not intended to replace DSH's model message/stream types.

## 5. Routing

```ts
export interface RouteRequest {
  readonly taskKind: string;
  readonly requiredCapabilities: readonly string[];
  readonly inputModalities: readonly string[];
  readonly qualityClass: "fast" | "balanced" | "high";
  readonly latencyClass: "interactive" | "normal" | "batch";
  readonly maxContextTokens?: number;
  readonly allowRemote: boolean;
  readonly taskId: string;
}

export interface RouteDecision {
  readonly providerId: string;
  readonly modelId: string;
  readonly reasonCodes: readonly string[];
  readonly fallback?: {
    readonly providerId: string;
    readonly modelId: string;
  };
  readonly admission: {
    readonly requireResourceCheck: boolean;
    readonly maxConcurrentModelLoads: number;
    readonly preserveContext: boolean;
  };
}
```

The router expresses a preference; the resource manager and security policies can reject the route. A routing result is not permission to execute tools.

## 6. Immutable task contract

```ts
export interface TaskContract {
  readonly taskId: string;
  readonly originalRequest: string;
  readonly constraints: readonly string[];
  readonly acceptanceCriteria: readonly AcceptanceCriterion[];
  readonly allowedCapabilities: readonly string[];
  readonly forbiddenActions: readonly string[];
  readonly workspaceRef?: string;
  readonly parentTaskId?: string;
  readonly contextRefs: readonly string[];
}
```

The original request and acceptance criteria must remain available to every delegated task. Summaries may be added, but never replace the original task contract. Any transformation must preserve task identity and a traceable link to the source contract.

## 7. Planner, specialist and verifier

```ts
export interface Planner {
  plan(task: TaskContract, context: TaskContext, signal?: AbortSignal): Promise<TaskPlan>;
}

export interface Specialist {
  readonly id: string;
  readonly capabilities: readonly string[];
  execute(
    task: TaskContract,
    assignment: SpecialistAssignment,
    signal?: AbortSignal,
  ): Promise<SpecialistResult>;
}

export interface Verifier {
  verify(
    task: TaskContract,
    result: SpecialistResult,
    signal?: AbortSignal,
  ): Promise<VerificationReport>;
}
```

`TaskPlan` must express dependencies, expected outputs, bounded attempts and stop conditions. A planner cannot mark work completed solely because a specialist returned a non-empty response.

## 8. Memory and context

```ts
export interface MemoryProvider {
  put(record: MemoryRecord, signal?: AbortSignal): Promise<MemoryRef>;
  get(ref: MemoryRef, signal?: AbortSignal): Promise<MemoryRecord | undefined>;
  search(query: MemoryQuery, signal?: AbortSignal): Promise<readonly MemoryHit[]>;
  delete(ref: MemoryRef, signal?: AbortSignal): Promise<void>;
}

export interface ContextPolicy {
  assemble(input: ContextInput, signal?: AbortSignal): Promise<AssembledContext>;
}

export interface CachePolicy {
  get<T>(key: CacheKey, signal?: AbortSignal): Promise<CacheResult<T>>;
  set<T>(key: CacheKey, value: T, metadata: CacheMetadata): Promise<void>;
  invalidate(selector: CacheSelector): Promise<void>;
}
```

Memory records require provenance, scope, timestamps, retention classification and schema version. Cache entries require security-aware keys and explicit invalidation. These interfaces do not define the internal engine KV format.

## 9. Resource management

```ts
export interface ResourceSnapshot {
  readonly devices: readonly {
    readonly id: string;
    readonly architecture: string;
    readonly totalVramMiB?: number;
    readonly freeVramMiB?: number;
  }[];
  readonly host: {
    readonly totalRamMiB: number;
    readonly availableRamMiB: number;
    readonly swapUsedMiB?: number;
  };
  readonly runningProviders: readonly {
    readonly providerId: string;
    readonly modelId?: string;
    readonly state: "starting" | "ready" | "busy" | "stopping" | "failed";
  }[];
}

export interface ResourceManager {
  snapshot(signal?: AbortSignal): Promise<ResourceSnapshot>;
  admit(request: ResourceRequest, signal?: AbortSignal): Promise<ResourceAdmission>;
  release(leaseId: string): Promise<void>;
}
```

Resource admission is a mandatory step before heavyweight model load or training launch. Estimates are conservative hints; live measurements and provider-reported requirements take precedence.

## 10. Event naming

Proposed LocalAMDAI event namespaces:

- `localamdai/route/selected`
- `localamdai/route/rejected`
- `localamdai/model/load-started`
- `localamdai/model/ready`
- `localamdai/model/unloaded`
- `localamdai/resource/pressure`
- `localamdai/task/created`
- `localamdai/task/delegated`
- `localamdai/task/verified`
- `localamdai/task/escalated`
- `localamdai/memory/hit`
- `localamdai/benchmark/completed`

Use DSH durable session events when an event represents a fact needed to reconstruct model-visible history. Use local plugin events for transient telemetry and lifecycle. Do not create duplicate durable logs that disagree with the DSH session record.

## 11. Versioning

- Version contracts independently from provider implementations.
- Add fields compatibly where possible; use explicit major-version changes for breaking semantics.
- Validate plugin config at mount time.
- Reject unknown critical capabilities rather than silently downgrading.
- Include provider and model identity in traces, but redact secrets and sensitive inputs.
