# SCRUM-27 Sprint 1 Requirements Traceability

**Record status:** RECORDED

**Traceability confidence:** PARTIAL

**Implementation and runtime validation:** NOT_RUN

## Scope and interpretation

This record maps the eight Sprint 1 delivery groups listed in Jira to the
available RF, RNF, and RTO inventory. It is a documentary traceability record;
it does not prove implementation, acceptance, deployment, or runtime behavior.

The source CSV has the columns `id`, `tag`, `text`, `line`, `status`, `reason`,
`owner`, and `acceptance`. It does not contain Jira issue keys, epic IDs, sprint
IDs, or delivery-group identifiers. The mappings below are therefore limited to
requirements whose owner or text explicitly names the corresponding service or
platform concern. They are not direct Jira-to-requirement links.

Terms such as `INCLUIDO / VALIDAR`, `INCLUIDO PARCIAL`, `DIFERIDO`,
`ARQUITECTURA OBJETIVO`, `OBJETIVO NO PROBADO`, `POC REQUERIDA`,
`EXCLUIDO MVP`, `GAP`, and `NOT_RUN` are non-passing states unless bounded
runtime evidence explicitly says otherwise.

## Sprint 1 delivery groups

The open Sprint 1 scope in Jira contains these epic-level delivery groups:

1. Architecture and delivery governance.
2. AWS foundation and Kubernetes platform.
3. Continuous integration and delivery gates.
4. Institutional identity service.
5. Versioned configuration service.
6. Mobile, web, and desktop integration.
7. n8n notification channel foundation.
8. Quality gates, environment promotion, and sprint closure.

## Requirements matrix

### 1. Architecture and delivery governance

**Mapping:** `GAP`

No RF, RNF, or RTO row explicitly owns governance deliverables such as ADRs,
roles, scope matrices, or delivery governance. `RF-INTG-01` through
`RF-INTG-09` cover platform and service contracts, but they do not establish a
direct requirement for the governance deliverable and are not claimed as its
mapping.

### 2. AWS foundation and Kubernetes platform

| Classification | Requirement IDs |
|---|---|
| `INCLUIDO / VALIDAR` | `RTO-IAC-01`–`RTO-IAC-06`; `RTO-NET-01`–`RTO-NET-06`; `RTO-DEV-05`, `RTO-DEV-06`; `RTO-SEC-01`–`RTO-SEC-03`; `RTO-STO-01` |
| `ARQUITECTURA OBJETIVO` | `RTO-HA-01`–`RTO-HA-05` |

The HA requirements remain target architecture. They are not current AWS,
Kubernetes, disaster-recovery, availability, RPO, or RTO evidence.

### 3. Continuous integration and delivery gates

| Classification | Requirement IDs |
|---|---|
| `INCLUIDO / VALIDAR` | `RTO-DEV-01`–`RTO-DEV-11`; `RTO-IAC-05`, `RTO-IAC-06`; `RTO-API-01` |

`RTO-DEV-01`, `RTO-DEV-02`, and `RTO-DEV-10` contain Turborepo or Astro
wording displaced by the latest MVP direction. Their inventory status is
preserved, but the displaced implementation wording is not adopted.

### 4. Institutional identity service

| Classification | Requirement IDs |
|---|---|
| `INCLUIDO / VALIDAR` | `RF-AUTH-01`–`RF-AUTH-08`; `RF-AUTH-10`–`RF-AUTH-18`; `RNF-SEC-09`; `RTO-SEC-02`, `RTO-SEC-04` |
| `INCLUIDO PARCIAL` | `RF-AUTH-09` |

### 5. Versioned configuration service

| Classification | Requirement IDs |
|---|---|
| `INCLUIDO / VALIDAR` | `RF-CFG-01`–`RF-CFG-03`; `RF-CFG-05`–`RF-CFG-12` |
| `DIFERIDO` | `RF-CFG-04` |

### 6. Mobile, web, and desktop integration

| Classification | Requirement IDs |
|---|---|
| `INCLUIDO / VALIDAR` | `RF-AUTH-13`; `RNF-COMP-02`, `RNF-COMP-03`; `RNF-USAB-03`, `RNF-USAB-04`; `RNF-FLEX-07`, `RNF-FLEX-08`; `RTO-DEV-02`–`RTO-DEV-04`; `RTO-NET-03`; `RNF-PERF-15` |
| `OBJETIVO NO PROBADO` | `RNF-USAB-01`, `RNF-USAB-05` |
| `POC REQUERIDA` | `RF-WASM-01`–`RF-WASM-05`; `RTO-WASM-01` |
| `EXCLUIDO MVP` | `RF-WEB-01`–`RF-WEB-04`; `RTO-WEB-01` |

Excluded web requirements are retained for traceability and are not Sprint 1
implementation scope.

### 7. n8n notification channel foundation

| Classification | Requirement IDs |
|---|---|
| `INCLUIDO CON CONTROL` | `RF-AUTO-01`–`RF-AUTO-08` |
| `INCLUIDO / VALIDAR` | `RF-NOTIF-01`, `RF-NOTIF-03`, `RF-NOTIF-04`, `RF-NOTIF-06`–`RF-NOTIF-08`, `RF-NOTIF-18`–`RF-NOTIF-22`; `RTO-REALTIME-01`–`RTO-REALTIME-03`; `RNF-PERF-08`; `RTO-NET-06`; `RNF-MAIN-05`; `RNF-FLEX-05`; `RTO-OBS-02` |
| `INCLUIDO PARCIAL` | `RF-NOTIF-02`, `RF-NOTIF-05` |

### 8. Quality gates, environment promotion, and sprint closure

| Classification | Requirement IDs |
|---|---|
| `INCLUIDO / VALIDAR` | `RTO-DEV-06`–`RTO-DEV-09`; `RTO-IAC-05`; `RTO-API-01`; `RTO-ENV-08`, `RTO-ENV-09`; `RNF-SEC-19`; `RTO-SEC-05`; `RTO-OBS-01`–`RTO-OBS-04` |
| `GAP` | No RF, RNF, or RTO explicitly maps to the sprint-closure ceremony itself |

## Reconciliation and limitations

- Requirements v2.5 were received. This record does not repeat the obsolete
  claim that F02 is missing.
- Both occurrences of `RF-NEWS-05` and `RF-NEWS-06` remain distinct. All four
  entries are `DIFERIDO` and are not mapped to these Sprint 1 groups.
- The 162-route API mapping remains candidate and partial; `RTO-API-01` does
  not certify API equivalence.
- A requirement appearing in this matrix is an alignment candidate, not proof
  that every Sprint 1 ticket satisfies it.
- Service, database, contract, UI, and E2E links remain ticket-level work. This
  group-level matrix does not replace those links.
- Real-election readiness, real personal data, legal or fiscal compliance,
  AWS availability, capacity above 100,000 users, WCAG compliance, RPO, and RTO
  remain unproven.

## Quality-gate applicability

This ticket adds only a Markdown traceability record. It changes no Java domain
behavior, architecture boundary, database integration, executable contract,
security control, infrastructure resource, or load-bearing endpoint.

Unit, ArchUnit, integration, contract, security, and load/stress tests are not
applicable to this change. No test is created merely to produce a passing
result, and no quality gate is reported as `PASS`.

## Acceptance result

| Acceptance item | Result |
|---|---|
| Eight Jira Sprint 1 delivery groups recorded | RECORDED |
| RF, RNF, and RTO candidates retain source classification | RECORDED |
| Missing direct Jira-to-requirement links disclosed | PARTIAL / GAP |
| Deferred, excluded, target, and PoC states kept non-passing | RECORDED |
| Duplicate `RF-NEWS-05` and `RF-NEWS-06` entries preserved | RECORDED |
| `docs/` kept read-only and excluded from the tracked deliverable | RECORDED |
| Ticket-level service, DB, contract, UI, and E2E links | PENDING |
| Implementation and runtime quality gates | NOT_RUN |

## Authoritative local sources

- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`.
- `docs/00_Gobierno/02_Contradicciones_y_ADR.md`.
- `docs/01_Producto/TRAZABILIDAD_RF_RNF_RTO.csv`.
- `docs/01_Producto/Requisitos_Trazados/`.
- `docs/14_Gestion/01_Backlog_de_implementacion_y_dependencias.md`.
- `infra/evidence/SCRUM-26-architecture-decisions-and-blockers.md`.

The local source files were read only and were not modified.
