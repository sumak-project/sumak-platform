# SCRUM-138 — Dependency resilience policy evidence

- **Record status:** `RECORDED`
- **Decision approval:** `PENDING`
- **Record date:** 2026-11-27
- **Jira:** SCRUM-138
- **Policy:** `architecture/decisions/ADR-0003-dependency-resilience-policy.md`
- **Runtime changes:** `NOT_RUN`
- **Runtime validation:** `NOT_RUN`

## Delivered scope

ADR-0003 records candidate dependency budgets, deadline propagation,
documented failure-containment mechanisms, uncertainty and reconciliation
invariants, dependency-specific rollout gates, and three Given/When/Then
fault-injection scenarios.

The policy explicitly distinguishes:

- candidate values from measured limits and SLAs;
- fail-closed authorization from business rejection;
- transient retry from unknown-outcome reconciliation; and
- policy/test design from runtime implementation.

No library, shared runtime preset, service implementation, AWS resource, or
environment was changed.

## Acceptance results

| Acceptance result | Status | Evidence |
| --- | --- | --- |
| Candidate operation budgets and propagated-deadline policy recorded | `RECORDED` | ADR-0003 decision table and invariants |
| Dependency-specific rollout and rollback criteria recorded | `RECORDED` | ADR-0003 rollout gate |
| Dependency-down scenario designed | `RECORDED` | ADR-0003 fault-injection scenarios |
| 50-percent-timeout scenario designed | `RECORDED` | ADR-0003 fault-injection scenarios |
| Unknown sensitive outcome does not become rejection or blind retry | `RECORDED` | ADR-0003 invariants and scenario |
| Runtime fault injection and measured latency evidence | `NOT_RUN` | No implemented business dependency adapter or representative runtime exists |
| Circuit-breaker implementation or broad rollout | `NOT_RUN` | Explicitly excluded; future bounded service ticket required |
| AWS, QA, and production validation | `NOT_RUN` | Outside scope and not authorized |

`RECORDED` means the policy or test scenario exists. It is not runtime `PASS`,
implementation approval, an SLA, availability evidence, or a capacity claim.

## Required future evidence

Each adopting service must attach the implementation version and environment,
sanitized synthetic workload, commands and configuration, latency
distribution, propagated-deadline observations, dependency-down and
50-percent-timeout results, duplicate-effect checks, recovery behavior,
metrics, rollback result, and reviewer.

Until that evidence exists, runtime categories remain `NOT_RUN` or use the
precise applicable `BLOCKED_*` state.

## Quality gate

This change contains Markdown policy and test design only. Unit, architecture,
integration, contract, security, and load/stress execution are not applicable
and remain `NOT_RUN`; no `PASS` is claimed. Applicable static validation is
content review against the authoritative references and `git diff --check`.

## Documentation impact

ADR-0003 and this evidence record are the tracked documentation deliverables.
No executable behavior, contract, setup, or operational procedure changed.
The ignored `docs/` source of truth was not modified.

## Authoritative references

- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`
- `docs/01_Producto/Requisitos_Trazados/RNF_SEC.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_NET.md`
- `docs/03_Microservicios/01_Catalogo.md`
- `docs/08_Seguridad/04_Identidad_AD_Cloudflare_y_operacion_segura.md`
- `docs/09_DevOps/03_Pipelines_migraciones_y_despiegues_por_ambiente.md`
- `docs/11_Contratos/01_Comunicacion_y_eventos.md`
- `docs/13_Pruebas/01_Plan_de_pruebas_y_calidad.md`
