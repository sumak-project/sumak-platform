# ADR-0003: Define Bounded Dependency Resilience Defaults

- **Record status:** `RECORDED`
- **Runtime approval:** `PENDING`
- **Decision date:** 2026-11-27
- **Jira:** SCRUM-138
- **Decision owner:** SUMAK platform architecture
- **Runtime evidence:** `NOT_RUN`

## Context

SUMAK needs consistent timeout, deadline, retry, and failure-containment
behavior across synchronous calls, asynchronous work, providers, databases,
LLM calls, and edge connections. The repository does not yet contain business
service implementations or representative dependency runtimes, so measured
defaults and fault-injection results are unavailable.

The source contracts already require propagated gRPC deadlines, bounded retry
with backoff and jitter, owner-controlled leases, reconciliation of uncertain
outcomes, bounded buffers, WebSocket backpressure, local ballot deadlines, and
health probes that do not depend on every external system. This decision
consolidates those mechanisms without claiming a production SLA or selecting a
runtime library.

## Decision

Adopt the following candidate policy for implementation and measurement by
future service tickets:

| Dependency class | Candidate operation budget | Required behavior |
| --- | --- | --- |
| Internal gRPC read | 2 seconds | Propagate the caller deadline; the callee must not extend it. |
| Client-facing BFF read | 5 seconds | Bound the complete request budget, including internal calls. |
| Business command | 5 seconds | Preserve idempotency and return an explicit uncertain state when the outcome cannot be established. |
| Authorized webhook call | 10 seconds | Validate signature and scope before work; retry only documented transient failures. |
| Worker or task | Per task envelope | Honor UTC `deadline`, lease, and `notBefore`; acknowledge only after durable owner persistence. |
| Database, provider, or LLM call | Dependency-specific and shorter than the caller budget | Reserve time for mapping, persistence, and a controlled response; measure before approval. |
| WSS connection | Compatible with the measured ALB idle timeout | Use authenticated heartbeat, bounded buffers, backpressure, slow-client close, reconnect, and resync. |

These values are **measurement candidates**, not SLAs, approvals, or evidence
of runtime behavior. Each implementation must derive smaller downstream
budgets from the remaining caller deadline rather than restarting the full
budget at every hop.

Failure containment uses only the mechanisms established by the source
contracts:

- bounded retry with exponential backoff and jitter for explicitly transient
  failures;
- a candidate maximum of three automatic task attempts before DLQ, subject to
  provider-specific measurement;
- bulkheads, bounded queues and buffers, backpressure, abstention, and
  dependency-independent health probes;
- reconciliation for unknown outcomes, event gaps, transaction identifiers,
  nonces, and owner cursors; and
- fail-closed authorization for sensitive actions.

A circuit-breaker library or shared runtime preset is not selected by this
ADR. A service may introduce one only in a bounded implementation ticket that
maps its states to the mechanisms above, supplies dependency-specific rollout
and rollback criteria, and records fault-injection evidence.

## Invariants

1. A timeout is a technical uncertainty, not a business rejection. In
   particular, it must not be converted to `FundsRejected`, a failed vote, or a
   successful write.
2. An unknown result is reconciled before retry. Blind retry is prohibited for
   non-idempotent effects, provider delivery, ledger anchors, finance, and
   voting.
3. Duplicate identifiers with the same digest produce no repeated effect.
   Duplicate identifiers with a different digest are integrity errors.
4. Event gaps pause dependent processing until an authorized snapshot or
   replay reconciles the gap.
5. Sensitive operations remain fail-closed when authentication,
   authorization, MFA, revocation, ownership, state, or inter-account
   prerequisites cannot be established.
6. Fail-closed does not authorize destructive compensation, rejection, or
   retry when the original outcome is unknown.
7. No retry path may bypass service ownership, create cross-owner SQL access,
   expose domain databases, or place PII, credentials, ballots, or reusable
   tokens in DLQ payloads.
8. Kafka, RabbitMQ, WSS, and scheduler mechanisms retain their documented
   ownership. This policy does not duplicate the retry/DLQ implementation
   scope owned by SCRUM-113.

## Dependency-specific rollout gate

Before enabling a resilience mechanism for a dependency, its implementation
ticket must record:

1. operation owner, idempotency key, deadline propagation, and uncertainty
   semantics;
2. transient and permanent error classification;
3. retry eligibility, backoff/jitter, maximum attempts, and DLQ or
   reconciliation owner;
4. queue, buffer, concurrency, and bulkhead limits;
5. observability that excludes secrets and personal or ballot data;
6. dependency-down and 50-percent-timeout fault-injection results;
7. recovery, half-open/probe behavior when applicable, rollback criteria, and
   alert ownership; and
8. measured latency distribution and remaining-budget behavior in the named
   environment and version.

No broad rollout is permitted from this policy alone.

## Fault-injection acceptance scenarios

### Dependency unavailable

**Given** an implemented dependency adapter with an approved error
classification and sanitized synthetic data, **when** the dependency is
unavailable for longer than the operation budget, **then** the caller:

- stops within its propagated deadline;
- performs only eligible bounded retries;
- contains concurrency and queue growth;
- preserves an unknown state when an effect may have occurred;
- sends eligible exhausted tasks to a sanitized DLQ or reconciliation path;
  and
- recovers through controlled probes without a simultaneous retry storm.

### Fifty percent of calls time out

**Given** representative synthetic traffic, **when** 50 percent of dependency
calls exceed their allotted downstream budget, **then** evidence must show:

- bounded caller latency and resource use;
- no deadline extension across hops;
- no duplicate business effect or silent event gap;
- sensitive writes fail closed while uncertain effects reconcile;
- health endpoints remain useful without depending on every external system;
  and
- recovery and rollback meet the dependency-specific criteria.

### Unknown sensitive outcome

**Given** a finance, voting, provider-delivery, or ledger operation whose
response is lost, **when** the caller cannot prove whether the owner committed
the effect, **then** it records an unknown or pending state, queries the
authoritative owner using the stable identifier, and does not translate the
timeout into rejection, success, or blind retry.

## Consequences

- Service tickets gain one reviewable baseline while retaining
  dependency-specific measurement and ownership.
- Call chains must reserve time for local work and controlled error handling.
- More explicit unknown states and reconciliation flows are required.
- Runtime configuration remains deliberately absent until an implemented
  adapter can prove it.
- This ADR changes no AWS resource, environment, contract, API, or database.

## Validation record

| Evidence | Status | Notes |
| --- | --- | --- |
| Policy and source-contract review | `RECORDED` | Candidate behavior and invariants are documented here. |
| Dependency-down fault injection | `NOT_RUN` | No implemented business dependency adapter exists. |
| 50-percent-timeout fault injection | `NOT_RUN` | No representative runtime or workload exists. |
| Candidate timeout measurement | `NOT_RUN` | Values remain candidates, not SLAs. |
| Circuit-breaker library evaluation | `NOT_RUN` | No library is selected by this ADR. |
| AWS, QA, or production validation | `NOT_RUN` | Outside scope and not authorized. |

## Documentation impact

This tracked ADR is the policy deliverable. It changes no runtime behavior,
setup, contract, or operation, so there is no other documentation impact. The
ignored `docs/` source of truth remains unchanged.

## Authoritative references

- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`
- `docs/01_Producto/Requisitos_Trazados/RNF_SEC.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_NET.md`
- `docs/03_Microservicios/01_Catalogo.md`
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`
- `docs/08_Seguridad/04_Identidad_AD_Cloudflare_y_operacion_segura.md`
- `docs/09_DevOps/03_Pipelines_migraciones_y_despiegues_por_ambiente.md`
- `docs/11_Contratos/01_Comunicacion_y_eventos.md`
- `docs/13_Pruebas/01_Plan_de_pruebas_y_calidad.md`
