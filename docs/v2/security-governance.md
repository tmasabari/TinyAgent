# TinyAgent v2 Security and Governance

## 1. Trust boundaries

- **Host boundary:** DSH process, Cordis services, local credentials and host-owned policy.
- **Model boundary:** model outputs and tool-call proposals are untrusted input.
- **Retrieval boundary:** files, web pages, repositories and external records may contain untrusted instructions.
- **Execution boundary:** shell, filesystem, browser, Docker and network tools can create side effects.
- **Provider boundary:** local inference engines and remote model APIs are separate trust domains.

## 2. Core rules

1. A model may propose an action; host policy authorizes it.
2. Local privacy/security screening must run before any cloud-bound operation when strict no-egress is required.
3. Tool permissions are explicit and scoped to the agent/session.
4. Use DSH sandbox and approval capabilities; do not create an alternate bypass.
5. Treat retrieved content as data, never as higher-priority instructions.
6. Secrets must use host credential facilities and must not enter prompts, logs or benchmark fixtures.
7. Every side-effecting operation needs an audit trace and bounded execution policy.
8. A failed or ambiguous safety check defaults to deny or human confirmation, according to policy.

## 3. Tool policy

Existing TinyAgent tools remain conceptually stable:

```json
{"source":"file | web | domain","query":"string"}
{"operation":"edit | os | web","param":"string"}
```

The DSH integration maps them to DSH tools. Preserve argument semantics during migration; any new structured schema requires a compatibility adapter and tests.

Execution controls should include:
- Path/workspace allowlists.
- Command and executable policy.
- Network allowlists and egress policy.
- Destructive-operation deny/confirm rules.
- Timeouts and output limits.
- Resource budgets.
- Idempotency and state checks for retries.

## 4. Long-horizon task safety

For terminal or infrastructure work:
- Run in a sandbox isolated from production.
- Verify production state has not changed.
- Verify sandbox state and outputs.
- Generate an explicit proposed remediation rather than applying it to production.
- Require approval for production mutation.
- Recheck authorization at execution time, not only during planning.

A specialist model is not a security boundary. A planner can instruct a specialist to perform an unsafe action; the host must prevent it.

## 5. Audit and events

Use transient plugin events for operational metrics. Use DSH durable session events for user-visible facts that must be reconstructable.

Audit fields should include task/session/agent IDs, provider/model IDs, tool identity, policy decision, approval identity, timestamps, result status and evidence references. Avoid recording secrets or unrestricted raw user content.

## 6. Plugin lifecycle

Every plugin must:
- Own its event listeners, service registrations, timers, child processes and resource leases.
- Dispose them on unload.
- Stop accepting work before releasing shared resources.
- Cancel or await in-flight work where required.
- Avoid orphan processes and duplicate provider registrations.

Lifecycle tests are mandatory for all resource-owning plugins.
