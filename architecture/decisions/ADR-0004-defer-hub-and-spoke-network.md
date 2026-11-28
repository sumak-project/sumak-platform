# ADR-0004: Defer the Hub-and-Spoke Network Topology

- **Record status:** `RECORDED`
- **Decision approval:** `PENDING`
- **Decision date:** 2026-11-27
- **Jira:** SCRUM-137
- **Decision owner:** SUMAK platform architecture
- **AWS-14 inter-account network PoC:** `PENDING`
- **Hub-and-spoke evaluation:** `NOT_RUN`
- **Infrastructure/AWS changes:** `NOT_RUN`

## Context

An instructor-proposed hub-and-spoke topology must be evaluated against SUMAK's
authoritative MVP baseline and Learner Lab constraints. The current baseline
uses ten isolated academic accounts, a VPC per account, non-overlapping CIDRs,
and per-account Terraform state and registries. It does not imply AWS
Organizations, inter-account routing, or cross-account IAM.

The proposal is non-authoritative and has no measured Learner Lab evidence.
AWS-14, the required inter-account network PoC, has not run, and no AWS mutation
or PoC execution was authorized for this ticket.

## Decision

Retain the isolated per-account VPC topology and defer hub-and-spoke adoption.
Hub-and-spoke remains a candidate that requires explicit authorization, a
measured AWS-14 PoC, decision-owner review, and a subsequent approval before any
implementation.

No compatibility, feasibility, availability, capacity, cost, security, or
production-readiness claim is made. `RECORDED` applies only to this ADR; it is
not `PASS`, approval, or runtime evidence.

## Compatibility assessment

| Candidate | Current disposition | Constraint or required evidence |
| --- | --- | --- |
| Transit Gateway hub-and-spoke | Deferred; `NOT_RUN` | Transit Gateway is not assumed in Learner Lab. It requires verified permissions, quotas, routing isolation, cost, cleanup, and an authorized PoC. |
| General VPC peering | Rejected for the baseline | RTO-NET-05 prohibits general peering between DEV, QA, and PROD. Any narrower exception requires documented flows, authorization, and measured evidence. |
| VPN or Direct Connect | Out of scope; `NOT_RUN` | Neither service nor an institutional network path may be assumed. |
| Cross-account IAM or `sts:AssumeRole` | Prohibited by the current baseline | Per-account state, ECR, and existing-role constraints apply; no custom cross-account role is authorized. |
| Authenticated application bridge | Conditional candidate | A bounded gRPC TLS/mTLS bridge over documented endpoints may be evaluated by AWS-14 without implying network-level trust. Same-account fallback must remain possible. |
| Isolated VPC per account | Retained baseline | Matches RTO-NET-01, RTO-IAC-03/05, RTO-ENV-02, and current Learner Lab constraints. |

## Activation gates and required evidence

Reconsideration may begin only after all of these conditions are met:

1. AWS mutation and AWS-14 execution receive explicit authorization.
2. The PoC plan defines the account, region, existing role, IaC revision,
   proposed flow, security boundaries, quotas, cost guardrails, and cleanup.
3. Tests use sanitized synthetic payloads and record observable routing,
   authentication, failure isolation, and teardown results.
4. Evidence records the date, actions, results, quotas, and sanitized errors or
   captures without exposing account identifiers, credentials, or secrets.
5. Blockers use precise labels such as `BLOCKED_AWS_PERMISSION`,
   `BLOCKED_QUOTA`, `BLOCKED_SECURITY`, or
   `BLOCKED_EXTERNAL_DEPENDENCY`; they are not bypassed.
6. A decision owner reviews the evidence and a subsequent ADR approves any
   departure from the isolated-account baseline.

## Boundaries and consequences

- This ADR creates no Terraform, AWS resource, route, IAM, state, ECR, secret,
  QA, or production change.
- No Transit Gateway, VPC peering, VPN, Direct Connect, Organizations, SCP,
  custom IAM role, IRSA, or `AssumeRole` is authorized.
- No shared-services dependency, cross-account state, registry, or secret
  centralization is introduced.
- No HA, RPO/RTO, capacity, compliance, or real-data claim is supported.
- An instructor reference is design input, not authorization or validation.
- The ignored `docs/` tree remains unchanged and authoritative.

## Validation record

| Evidence | Status | Notes |
| --- | --- | --- |
| Source precedence and constraint comparison | `REVIEWED` | The proposal was compared with the authoritative sources below. |
| Bounded architecture decision | `RECORDED` | The baseline is retained and activation gates are recorded. |
| Decision approval | `PENDING` | No hub-and-spoke topology is approved. |
| Authorized AWS-14 PoC | `PENDING` | Authorization and an execution plan are required. |
| Hub-and-spoke runtime feasibility | `NOT_RUN` | No AWS mutation or runtime test occurred. |
| TGW, peering, VPN/Direct Connect, or cross-account IAM validation | `NOT_RUN` | These mechanisms are excluded or unproven. |

This is a Markdown-only architecture decision. Unit, architecture, integration,
contract, security, and load/stress test categories are not applicable and are
`NOT_RUN`; no `PASS` is claimed. `git diff --check` and content review against
the cited sources are the applicable static validation.

## Documentation impact

This tracked ADR and its evidence record are the documentation deliverables.
They change no contract, setup, runtime, or operational behavior, so there is no
other documentation impact. Authoritative `docs/` sources were not modified.

## Authoritative references

- `docs/00_Gobierno/02_Contradicciones_y_ADR.md`
- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_HA.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_IAC.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_NET.md`
- `docs/05_Tecnologias/02_Fichas_de_decision_por_tecnologia.md`
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`
- `docs/06_AWS/03_Mapa_de_recursos_y_dependencias_por_cuenta.md`
- `docs/06_AWS/04_PoC_y_registro_de_decisiones_bloqueantes.md`
- `docs/08_Seguridad/02_Continuidad_y_backups.md`
- `docs/13_Pruebas/01_Plan_de_pruebas_y_calidad.md`
