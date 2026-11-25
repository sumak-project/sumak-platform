# SCRUM-26 Sprint 1 Architecture Decisions and Blockers

**Record status:** RECORDED

**Architecture approval:** PENDING

**Runtime validation:** NOT_RUN, except for the bounded evidence referenced
below

## Scope and status meaning

This record captures the current Sprint 1 architecture direction and unresolved
blockers. It does not approve an ADR, implement the architecture, certify the
candidate API mapping, or provide runtime evidence.

The source precedence used here is:

1. Latest explicit MVP direction.
2. Undisplaced v2.5 requirements.
3. Learner Lab v1.2 limits.
4. Original database and API designs.
5. The v2.0 redesign.

Terms such as `propuesto`, `PENDIENTE`, `PARCIAL`, `NOT_RUN`, and `BLOCKED_*`
are preserved as non-passing states. A document or screenshot is not runtime
evidence.

## Proposed architecture decisions

| ID | Recorded direction | Status | Authoritative source |
|---|---|---|---|
| K01 | Use a Java and Spring Boot Gradle monorepo. Do not split the platform into Turborepo or multiple repositories. | PENDING approval and implementation | `docs/00_Gobierno/02_Contradicciones_y_ADR.md`, K01; `docs/09_DevOps/01_Monorepo_Gradle.md`, target monorepo |
| K02 | Use GraphQL for clients, gRPC internally, Kafka for facts and replay, RabbitMQ for work, WSS for notifications, and HTTP only for authorized webhooks or technical interfaces. Do not introduce business REST for Swagger. | PENDING implementation and validation | `docs/00_Gobierno/02_Contradicciones_y_ADR.md`, K02; `docs/04_Arquitectura/01_Vistas_y_patrones.md`, communication views; `docs/05_Tecnologias/01_Inventario_y_decisiones.md`, protocol decisions |
| K03 | Use React Native for mobile, React for the administrative web application served from protected S3, and Electron for desktop. Astro and a citizen web portal are excluded. | PENDING implementation and validation | `docs/00_Gobierno/02_Contradicciones_y_ADR.md`, K03 and K19; `docs/05_Tecnologias/01_Inventario_y_decisiones.md`, client decisions |
| K04 | Integrate institutional AD through a Keycloak OIDC broker and keep the citizen realm separate. AD is not AWS IAM. | PENDING security review and implementation | `docs/00_Gobierno/02_Contradicciones_y_ADR.md`, K04 |
| K05 | Preserve 22 service owners, 19 independent PostgreSQL databases, and 3 DynamoDB tables. Each owner controls its persistence; cross-owner SQL, foreign keys, migrations, shared JPA entities, and shared domain DTOs are forbidden. | PENDING implementation and architecture-gate execution | `docs/00_Gobierno/02_Contradicciones_y_ADR.md`, K05 and K06; `docs/06_AWS/01_Cuentas_red_y_capacidad.md`, persistence allocation |
| K06 | Keep voter eligibility, anonymous ballot, and tally stores and services separate. Cryptographic review remains required. | PENDING cryptographic review and implementation | `docs/00_Gobierno/02_Contradicciones_y_ADR.md`, K13 |
| K07 | Treat more than 100,000 concurrent users as a design and measurement target only. No demonstrated capacity result exists. | NOT_RUN | `docs/00_Gobierno/02_Contradicciones_y_ADR.md`, K07; `docs/00_Gobierno/03_Matriz_cumplimiento.md`, R17 |
| K08 | Use ten isolated accounts in the target design and keep DEV, QA, and PROD isolated. Current work is limited to DEV; QA and PROD are not active environments. | PENDING target implementation | `docs/00_Gobierno/02_Contradicciones_y_ADR.md`, K08 and K16; `docs/06_AWS/01_Cuentas_red_y_capacidad.md`, account model |
| K09 | Bind DEV infrastructure to Learner Lab limits: `us-east-1` primary, `us-west-2` DR, no more than 9 running EC2 instances per account, no more than 32 running EC2 vCPU per region, RDS no larger than `medium` with 100 GB `gp2`, and pre-provisioned IAM roles only. | Bounded constraints validated by SCRUM-30; target infrastructure not provisioned | `docs/06_AWS/01_Cuentas_red_y_capacidad.md`, Learner Lab limits; `infra/evidence/SCRUM-30-learner-lab-validation.md` |
| K10 | Keep Kafka facts and RabbitMQ work distinct; MQTT is excluded. Use n8n for field and Telegram notification integration. | PENDING implementation and validation | `docs/00_Gobierno/02_Contradicciones_y_ADR.md`, K09 and K10; `docs/05_Tecnologias/01_Inventario_y_decisiones.md`, messaging decisions |
| K11 | Defer NEWS, SURV, and MEET capabilities; retire MINU; keep IA, TTS, and MCP choices behind explicit ADR review. | PENDING product and ADR approval | `docs/00_Gobierno/02_Contradicciones_y_ADR.md`, K11 and K14 |
| K12 | Serve the administrative web application through Cloudflare with a protected S3 origin, not EC2 hosting. Prefer approved open-source alternatives such as OpenSearch OSS, Besu, and MapLibre rather than unsupported managed substitutions. | PENDING implementation and validation | `docs/00_Gobierno/02_Contradicciones_y_ADR.md`, K12 and K18 |
| K13 | Apply microservices, event-driven architecture, CQRS, hexagonal architecture, 17 DDD bounded contexts, outbox/inbox, and saga patterns. | PENDING implementation and architecture-gate execution | `docs/04_Arquitectura/01_Vistas_y_patrones.md`, architecture patterns; `docs/00_Gobierno/03_Matriz_cumplimiento.md`, R08 and R09 |
| K14 | Use a same-account versioned S3 Terraform backend with native `use_lockfile = true` locking. Do not add a DynamoDB lock table or cross-account role. | Bounded SCRUM-37 implementation PASS; multi-writer behavior NOT_RUN | `docs/05_Tecnologias/01_Inventario_y_decisiones.md`, Terraform state decision; `infra/evidence/SCRUM-37-terraform-state-backend.md` |

All deliverables and technical artifacts remain in English. No budget, approval,
capacity, compliance, or readiness result is inferred from these recorded
directions.

## Unresolved blockers and evidence states

| Area | State | Blocker or limitation |
|---|---|---|
| Architecture approval | PENDING | Each ADR still requires an identified reviewer, author, and approval date. This record is not approval. |
| PoC program | PENDIENTE | The initial PoC state is pending. Failed execution must use `BLOCKED_AWS_PERMISSION`, `BLOCKED_QUOTA`, `BLOCKED_SECURITY`, or `BLOCKED_EXTERNAL_DEPENDENCY` as applicable. A local container does not certify an AWS service or DR. |
| Quality gates | NOT_RUN | Unit, architecture, integration, contract, security, and load/stress evidence has not been executed for this documentation-only record. Never report `PASS` merely because a test or record exists. |
| API reconciliation | PARCIAL, PENDIENTE DE VALIDACIÓN FILA A FILA | The candidate mapping of 162 routes is not certified as equivalent. Historical route counts do not supersede the current limitation. |
| Real elections and personal data | BLOCKED_SECURITY | No real election or real personal data is authorized without protocol, role, privacy, cryptographic, and measured security evidence. |
| AWS deployment | BLOCKED_AWS_PERMISSION | Provisioning requires an authorized bounded PoC, reviewed Terraform plan, cleanup plan, and confirmed permissions. |
| Legal and fiscal behavior | BLOCKED_EXTERNAL_DEPENDENCY | Accounting, fiscal, transparency, and electoral-role behavior requires external legal validation. |
| Capacity target | NOT_RUN | More than 100,000 concurrent users remains a design target with no measured result. |
| Availability and recovery | NOT_RUN | AWS availability, cross-region recovery, HA, RPO, and RTO are not demonstrated. |
| Accessibility | NOT_RUN | WCAG compliance is not demonstrated. |
| F07 source | BLOCKED_EXTERNAL_DEPENDENCY | The complete authoritative F07 source is absent; only its hash and Confluence reference are recorded locally. |
| Environment identity | BLOCKED_AWS_PERMISSION | No account-to-environment evidence distinguishes `sumak-dev` from `sumak-dev-integration`. |
| DEV platform resources | PENDIENTE | The target DEV VPC, EKS, ALB, private RDS, ECR, SSM, and analytics resources are not provisioned. |
| Terraform lock contention | NOT_RUN | Native lock-object permissions passed under SCRUM-37, but no real concurrent two-writer Terraform test was run. |
| Terraform KMS and DR | NOT_RUN | SSE-KMS permissions, cross-region recovery, RPO/RTO, and production readiness remain outside the SCRUM-37 PASS boundary. |
| AWSCC policy coverage | PENDIENTE | Trivy did not report the AWSCC bucket module as a separate target, so its result is not complete AWSCC policy coverage. |

## Quality-gate applicability

This ticket changes only this Markdown evidence record. It introduces no Java
domain behavior, architecture boundary, database integration, executable
contract, runtime security surface, or load-bearing endpoint. Unit, ArchUnit,
integration, contract, security, and load/stress tests are therefore not
applicable to the change. No test was created merely to produce a passing
result, and no quality gate is reported as `PASS`.

The `BLOCKED_AWS_PERMISSION`, `BLOCKED_QUOTA`, `BLOCKED_SECURITY`, and
`BLOCKED_EXTERNAL_DEPENDENCY` terms above preserve the PoC evidence vocabulary.
They are not promotion-gate results. Promotion evidence remains `NOT_RUN`.

## Existing bounded runtime evidence

### SCRUM-30

`infra/evidence/SCRUM-30-learner-lab-validation.md` records a bounded `PASS` for
Learner Lab constraints, selected role and quota observations, controlled
`iam:PassRole` policy simulation, PostgreSQL class availability, and residual
EC2 cleanup.

That `PASS` is not runtime proof of EKS, RDS, ALB, availability, capacity,
RPO/RTO, compliance, or production readiness. Direct `GetServiceQuota` remained
denied, non-project regions were not exhaustively inventoried, and the target
DEV resources were not provisioned.

### SCRUM-37

`infra/evidence/SCRUM-37-terraform-state-backend.md` records a bounded `PASS`
for the same-account DEV S3 backend, remote Terraform initialization, reviewed
plan and apply, state adoption, no-drift plan, and lock-object permissions.

That `PASS` does not validate concurrent writer contention, cross-region
recovery, RPO/RTO, production readiness, KMS permissions, or complete AWSCC
policy coverage. The real two-writer contention test remains `NOT_RUN`.

## Reconciliation notes

- Requirements v2.5 were received. The obsolete claim that F02 is missing is
  not repeated.
- Both occurrences of `RF-NEWS-05` and `RF-NEWS-06` remain intentional and are
  not deduplicated.
- The current API reconciliation limitation supersedes historical claims that
  a route inventory was complete.
- No current decision overrides persistence ownership, anonymous-ballot
  separation, or the protocol split.

## Acceptance result

| Acceptance item | Result |
|---|---|
| Architecture directions recorded with authoritative sources | RECORDED |
| Proposed directions distinguished from bounded runtime evidence | RECORDED |
| Unresolved blockers retain non-passing status vocabulary | RECORDED |
| Historical F02 and API-count conflicts reconciled | RECORDED |
| `docs/` kept read-only and excluded from the tracked deliverable | RECORDED |
| Architecture approval | PENDING |
| Runtime and quality-gate execution for this record | NOT_RUN |

## Authoritative local sources

- `docs/00_Gobierno/02_Contradicciones_y_ADR.md`.
- `docs/00_Gobierno/03_Matriz_cumplimiento.md`.
- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`.
- `docs/00_Gobierno/05_Diagnostico_de_lagunas_v2_0.md`.
- `docs/00_Gobierno/06_Criterios_de_cierre_documental_para_diagramas.md`.
- `docs/04_Arquitectura/01_Vistas_y_patrones.md`.
- `docs/05_Tecnologias/01_Inventario_y_decisiones.md`.
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`.
- `docs/06_AWS/04_PoC_y_registro_de_decisiones_bloqueantes.md`.
- `docs/11_Contratos/06_Verificacion_API_v2_5_1_y_alcance_GraphQL.md`.
- `docs/13_Pruebas/01_Plan_de_pruebas_y_calidad.md`.

The local source files were read only and were not modified.
