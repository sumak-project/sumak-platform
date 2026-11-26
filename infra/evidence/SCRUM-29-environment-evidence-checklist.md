# SCRUM-29 Environment Evidence Checklist

**Record status:** RECORDED

**Promotion execution:** NOT_RUN

**Active environment:** DEV only

## Purpose and evidence rules

This checklist defines the minimum evidence required to assess DEV work and any
future promotion to QA or PROD. It does not authorize a promotion, activate an
environment, or turn documentation into runtime proof.

`PASS` is allowed only when the named command or tool was executed and its
observable result and versioned evidence are linked. `NOT_RUN`, `FAIL`,
`BLOCKED_PERMISSIONS`, `BLOCKED_CAPACITY`, `BLOCKED_CONTRACT`, and
`WAIVED_WITH_ADR` are non-passing outcomes. A waiver requires an approved ADR
and is not equivalent to `PASS`.

For bounded AWS proofs of concept, the more specific
`BLOCKED_AWS_PERMISSION`, `BLOCKED_QUOTA`, `BLOCKED_SECURITY`, and
`BLOCKED_EXTERNAL_DEPENDENCY` outcomes may be recorded. They do not satisfy a
promotion gate.

## Evidence bundle required for every execution

- [ ] Jira issue and source commit are identified.
- [ ] Immutable OCI digest is recorded when an image is produced.
- [ ] Environment, AWS account, region, and execution timestamp are recorded.
- [ ] Database schema and contract versions are recorded or explicitly marked
      not applicable.
- [ ] A versioned, reproducible synthetic dataset is identified.
- [ ] Exact commands, tools, and relevant load level are recorded.
- [ ] Observable results and versioned evidence links are attached.
- [ ] The reviewer and approval decision are recorded.
- [ ] Secrets, production credentials, and real personal data are absent.
- [ ] Claims remain within the measured evidence boundary.

The machine-readable DEV-to-QA record starts from
`config/quality-gates/promotion-evidence.template.json` and is checked with:

```bash
python3 config/quality-gates/validate_promotion.py <evidence.json>
```

The validator is fail-closed. Promotion is blocked unless every mandatory gate
is `PASS` with command, observed result, and evidence, or has a complete
`WAIVED_WITH_ADR` record.

## DEV checklist

DEV is the only active working environment in Sprint 1.

| Check | Required evidence | Current Sprint 1 state |
|---|---|---|
| Source and artifact identity | Commit, workflow run, immutable digest, and artifact provenance | `PARTIAL`; repository evidence exists, complete promotion evidence does not |
| Unit | Executed tests for implemented domain behavior | `NOT_RUN` Sprint-wide |
| Architecture | Executed dependency and ownership boundary rules | `NOT_RUN` |
| Integration | Executed database and broker tests against applicable dependencies | `NOT_RUN` |
| Contract | Compiler and compatibility results for applicable versioned contracts | `NOT_RUN` |
| Security | Dependency, secret, image, authorization, and security-test results | `NOT_RUN` |
| Load and stress | Measured latency, errors, throughput, and saturation | `NOT_RUN` |
| Infrastructure | Format, validate, policy, reviewed plan, authorized apply, no-drift, and cleanup evidence | `PARTIAL`; bounded SCRUM-37 evidence only |
| Learner Lab limits | Role, quota, instance, RDS, and cleanup observations | Bounded `PASS` in SCRUM-30 only |
| Promotion | Complete fail-closed evidence and explicit QA approval | `NOT_RUN` |

The bounded `PASS` results in SCRUM-30 and SCRUM-37 do not prove EKS, RDS, ALB,
capacity, availability, disaster recovery, RPO/RTO, compliance, or production
readiness.

## QA promotion checklist

QA remains inactive and reserved. A DEV-to-QA promotion must not begin until:

- [ ] All six mandatory gates (`unit`, `architecture`, `integration`,
      `contract`, `security`, and `load_stress`) satisfy the fail-closed
      promotion validator.
- [ ] The exact immutable artifact tested in DEV is selected.
- [ ] Explicit QA promotion approval is recorded.
- [ ] QA uses its own account credentials, network boundaries, datasets,
      secrets, and encryption material.
- [ ] No DEV or QA role can read a production data lake or reuse PROD
      credentials or keys.
- [ ] Database and contract compatibility evidence is attached.
- [ ] Deployment, rollback, smoke-test, and cleanup commands are recorded.
- [ ] The resulting QA evidence bundle identifies observed results and reviewer.

**Current result:** `NOT_RUN`. QA is not configured, deployed, or reported as
active.

## PROD promotion checklist

PROD remains inactive and reserved. A QA-to-PROD promotion must not begin until:

- [ ] The exact artifact has complete, approved QA evidence.
- [ ] Every required lower-environment gate remains valid for that artifact.
- [ ] Explicit dual approval is recorded.
- [ ] Execution occurs in the destination account with its own temporary
      credentials and without cross-account `sts:AssumeRole`.
- [ ] PROD secrets, keys, data, network paths, and roles are isolated.
- [ ] No real data is copied into lower environments and no direct production
      restoration is used as test setup.
- [ ] Only authorized health, read-only, or bounded smoke checks are planned.
- [ ] Rollback, recovery, cleanup, and reviewer evidence are attached.
- [ ] Any cost statement is based on observed use rather than an unsupported
      annual forecast.

**Current result:** `NOT_RUN`. PROD is not configured, deployed, or reported as
active.

## Sprint closure checklist

- [ ] Every included Jira issue is Done or has an explicitly accepted blocker.
- [ ] Every delivered artifact is linked to its issue and bounded evidence.
- [ ] RF, RNF, and RTO links are recorded without inventing traceability.
- [ ] Applicable service, database, contract, UI, and E2E links are recorded.
- [ ] Every applicable quality gate has an evidence-backed outcome.
- [ ] Deferred and excluded work remains outside implementation claims.
- [ ] Every bounded AWS proof has reviewed cleanup evidence.
- [ ] No approval, compliance, capacity, availability, accessibility, recovery,
      or readiness claim exceeds measured evidence.
- [ ] QA and PROD remain inactive until their gates and authorizations exist.

**Current closure result:** `PENDING`. This checklist defines closure evidence;
it does not report Sprint 1 as closed.

## Quality-gate applicability for SCRUM-29

This ticket adds only this Markdown governance record. It changes no Java
behavior, architecture boundary, database integration, executable contract,
security control, infrastructure resource, or load-bearing endpoint.

Unit, ArchUnit, integration, contract, security, and load/stress tests are not
applicable to this documentation-only change. No test is added merely to create
a passing result, and no gate is reported as `PASS`.

## Acceptance result

| Acceptance item | Result |
|---|---|
| Shared evidence bundle defined | RECORDED |
| DEV evidence checklist and bounded current states recorded | RECORDED |
| QA promotion prerequisites defined without activating QA | RECORDED |
| PROD promotion prerequisites defined without activating PROD | RECORDED |
| Fail-closed validator and template linked | RECORDED |
| Sprint closure checklist defined | RECORDED |
| Promotion execution | NOT_RUN |
| Sprint closure | PENDING |
| `docs/` kept read-only and excluded from the tracked deliverable | RECORDED |

## Authoritative local sources

- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`.
- `docs/01_Producto/Requisitos_Trazados/RTO_DEV.md`.
- `docs/01_Producto/Requisitos_Trazados/RTO_ENV.md`.
- `docs/09_DevOps/02_CI_CD_operacion_Jira.md`.
- `docs/13_Pruebas/01_Plan_de_pruebas_y_calidad.md`.
- `docs/14_Gestion/02_Evidencias_coste_y_cierre.md`.
- `config/quality-gates/promotion-evidence.template.json`.
- `config/quality-gates/validate_promotion.py`.
- `infra/evidence/SCRUM-28-sprint-1-goal-scope-and-acceptance-gates.md`.
- `infra/evidence/SCRUM-30-learner-lab-validation.md`.
- `infra/evidence/SCRUM-37-terraform-state-backend.md`.

The local source files were read only and were not modified.
