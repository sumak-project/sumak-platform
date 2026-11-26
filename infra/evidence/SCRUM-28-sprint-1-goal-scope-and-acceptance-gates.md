# SCRUM-28 Sprint 1 Goal, Scope, and Acceptance Gates

**Record status:** RECORDED

**Sprint goal approval:** PENDING

**Implementation and runtime validation:** NOT_RUN, except for bounded evidence
explicitly referenced below

## Authority and status meaning

This record uses the following source precedence:

1. Latest explicit MVP direction.
2. Undisplaced v2.5 requirements.
3. Learner Lab v1.2 limits.
4. Original database and API designs.
5. The v2.0 redesign.

Requirements v2.5 were received. This record does not repeat the obsolete claim
that F02 is missing. Requirement classifications and architecture proposals are
not implementation, approval, or runtime evidence.

`RECORDED`, `PENDING`, `PARTIAL`, `GAP`, `NOT_RUN`, `PENDIENTE`, `DIFERIDO`,
`EXCLUIDO MVP`, `OBJETIVO NO PROBADO`, `ARQUITECTURA OBJETIVO`, and
`POC REQUERIDA` are non-passing states.

## Proposed Sprint 1 goal

Record and deliver a governed, testable foundation for a bounded SUMAK MVP
demonstration that connects the municipal government and citizens through
budget and public-works transparency, democratic participation, incident
reporting, notifications, and auditable actions.

Within authorized Learner Lab limits, Sprint 1 prepares the architecture,
delivery controls, DEV platform foundation, identity and configuration
boundaries, client integration direction, notification automation, and quality
evidence needed to demonstrate selected financial, mobile publication,
synthetic voting, incident, notification, field automation, search, Besu,
Athena, and AI-agent paths in later bounded increments.

The institutional architecture is planned as a target. Sprint 1 may demonstrate
only authorized subsets and does not claim that the complete platform, target
capacity, or production environments exist.

## In-scope delivery groups

The Jira Sprint 1 scope records these eight delivery groups:

1. **Architecture and delivery governance**
   - Record proposed architecture decisions, blockers, source precedence,
     requirement traceability, scope, exclusions, and evidence vocabulary.
   - Keep architecture approval `PENDING` until identified reviewers approve
     the applicable decisions.
2. **AWS foundation and Kubernetes platform**
   - Prepare bounded DEV infrastructure and Kubernetes foundations compatible
     with Learner Lab permissions, quotas, cleanup, and cost constraints.
   - Treat HA, DR, cross-region recovery, RPO, and RTO as target architecture,
     not demonstrated behavior.
3. **Continuous integration and delivery gates**
   - Define and automate repository, contract, dependency, security, artifact,
     infrastructure, and promotion checks where the corresponding components
     exist.
4. **Institutional identity service**
   - Establish the service boundary and the Keycloak OIDC broker direction for
     institutional AD while keeping citizen identity separate.
5. **Versioned configuration service**
   - Establish ownership and versioning boundaries for configuration without
     cross-service persistence coupling.
6. **Mobile, web, and desktop integration**
   - Prepare React Native mobile, protected React administration, and Electron
     desktop integration boundaries.
   - Retain excluded or PoC-only client requirements as traceability entries,
     not implemented scope.
7. **n8n notification channel foundation**
   - Establish controlled n8n and notification integration boundaries without
     treating external-channel connectivity as proven.
8. **Quality gates, environment promotion, and sprint closure**
   - Define evidence requirements and closure criteria.
   - Current execution is DEV-only. QA and PROD remain reserved targets and
     must not be configured, deployed, or reported as active in this sprint.

The group-level requirements matrix is recorded in
`infra/evidence/SCRUM-27-sprint-1-requirements-traceability.md`. Its confidence
is `PARTIAL`: the source inventory does not directly link Jira issues to
requirements, and ticket-level service, database, contract, UI, and E2E links
remain `PENDING`.

## Explicit exclusions and non-goals

Sprint 1 does not:

- authorize or certify a real election, real personal data, or legally binding
  democratic participation;
- certify COOTAD, LOPDP, electoral, accounting, fiscal, transparency, or
  retention compliance;
- demonstrate more than 100,000 concurrent users;
- demonstrate HA, DR, cross-region recovery, availability, RPO, or RTO;
- activate, configure, merge into, or deploy QA or PROD;
- claim that the target ten-account model is active;
- claim measured annual cost or production readiness;
- certify WCAG accessibility;
- certify the candidate 162-route API mapping as equivalent;
- include the Astro citizen portal, news, surveys, meetings, attendance, or
  withdrawn minutes capabilities;
- convert `DIFERIDO`, `EXCLUIDO MVP`, `POC REQUERIDA`, or
  `ARQUITECTURA OBJETIVO` requirements into implementation commitments;
- treat a document, screenshot, local container, or successful local command as
  proof of an AWS service, complete security posture, or disaster recovery.

Both occurrences of `RF-NEWS-05` and `RF-NEWS-06` remain distinct and
`DIFERIDO`.

## Environment and Learner Lab boundaries

`dev` is the only active working environment. Bounded AWS work must respect:

- no more than 9 running EC2 instances per account across regions;
- no more than 32 running EC2 vCPU per region;
- RDS no larger than `medium` with no more than 100 GB `gp2`;
- pre-provisioned IAM roles only;
- reviewed cleanup and recovery procedures for every bounded PoC.

SCRUM-30 records a bounded `PASS` for selected Learner Lab constraints, roles,
quota observations, controlled `iam:PassRole` simulation, RDS class
availability, and cleanup. It does not prove that DEV EKS, RDS, ALB, capacity,
availability, recovery, or production readiness exists.

SCRUM-37 records a bounded `PASS` for the same-account DEV S3 Terraform backend,
initialization, reviewed plan and apply, state adoption, no-drift planning, and
lock-object permissions. Concurrent writer contention, SSE-KMS, DR, RPO/RTO,
production readiness, and complete AWSCC policy coverage remain `NOT_RUN`,
outside scope, or `PENDIENTE`.

## Acceptance gates

A gate is satisfied only by the evidence named for that gate. Documentation
alone cannot produce `PASS`.

| Gate | Required evidence | Current state |
|---|---|---|
| Governance | Source precedence, decisions, blockers, requirement mapping, scope, exclusions, and named approval owner | `PARTIAL`; approval `PENDING` |
| Unit | Executed unit tests for implemented domain behavior | `NOT_RUN` for Sprint-wide implementation |
| Architecture | Executed architecture rules for service, domain, adapter, persistence, and ownership boundaries | `NOT_RUN` |
| Integration | Executed SQL and broker integration tests against applicable real dependencies | `NOT_RUN` |
| Contract | Compiler and compatibility validation for applicable GraphQL, Protobuf, AsyncAPI, and authorized HTTP contracts | `NOT_RUN` |
| Security | Dependency, secret, image, authorization, and security-test evidence for applicable artifacts | `NOT_RUN` |
| E2E | Executed, traceable user journeys with ticket and requirement links | `NOT_RUN` |
| Load and stress | Measured capacity, latency, error, and saturation results | `NOT_RUN` |
| Resiliency and DR | Failure, recovery, backup, restore, RPO, and RTO measurements | `NOT_RUN` |
| Accessibility | Measured accessibility results for applicable clients | `NOT_RUN` |
| Infrastructure | Terraform format, validate, policy, reviewed plan, authorized apply, no-drift, and cleanup evidence | `PARTIAL`; bounded SCRUM-37 evidence only |
| CI/CD | Lint, tests, contracts, dependency analysis, image scan, secret controls, security checks, and artifact build where applicable | `PARTIAL`; repository validation is not full promotion evidence |
| Promotion | Successful lower-environment gates and explicit approval before each target promotion | `NOT_RUN`; QA and PROD inactive |
| Closure | Every included Jira item has explicit evidence or an accepted non-passing state and no result exceeds its evidence boundary | `PENDING` |

Allowed gate outcomes are `NOT_RUN`, `PASS`, `FAIL`,
`BLOCKED_PERMISSIONS`, `BLOCKED_CAPACITY`, `BLOCKED_CONTRACT`, and
`WAIVED_WITH_ADR`. Bounded PoCs may additionally use
`BLOCKED_AWS_PERMISSION`, `BLOCKED_QUOTA`, `BLOCKED_SECURITY`, and
`BLOCKED_EXTERNAL_DEPENDENCY`.

`WAIVED_WITH_ADR` requires an explicit ADR and does not mean `PASS`.

## Sprint closure conditions

Sprint 1 may be recorded as closed only when:

1. Every included Jira ticket is `Done` or has an explicit accepted blocker.
2. Every delivered artifact is linked to its ticket and bounded evidence.
3. Applicable RF, RNF, and RTO links are recorded without inventing direct
   traceability.
4. Applicable service, database, contract, UI, and E2E links are recorded.
5. Every applicable quality gate has an evidence-backed outcome.
6. Deferred and excluded items remain outside implementation claims.
7. AWS resources created by bounded PoCs have reviewed cleanup evidence.
8. No claim of approval, compliance, availability, capacity, accessibility,
   recovery, or readiness exceeds measured evidence.
9. QA and PROD remain inactive until their required gates and authorizations
   exist.

These conditions define closure criteria; they do not report that Sprint 1 is
currently closed.

## Unresolved blockers and gaps

- Architecture approval: `PENDING`.
- PoC program: `PENDIENTE`.
- Sprint-wide quality gates: `NOT_RUN`.
- API reconciliation: `PARCIAL`, pending row-by-row validation.
- Real elections and personal data: `BLOCKED_SECURITY`.
- AWS deployment beyond authorized bounded work: `BLOCKED_AWS_PERMISSION`.
- Legal and fiscal validation: `BLOCKED_EXTERNAL_DEPENDENCY`.
- Capacity, availability, recovery, accessibility, RPO, and RTO: `NOT_RUN`.
- Complete F07 source: `BLOCKED_EXTERNAL_DEPENDENCY`.
- DEV environment identity and account evidence: `BLOCKED_AWS_PERMISSION`.
- Target DEV resources: `PENDIENTE`.
- Terraform contention, KMS, and DR evidence: `NOT_RUN`.
- Complete AWSCC policy coverage: `PENDIENTE`.
- Signed university rubric, publication rules, retention policy, external
  agreements, and broader AWS test results: `PENDIENTE`.
- Direct Jira-to-requirement links and ticket-level service, database,
  contract, UI, and E2E links: `PARTIAL / GAP`.

## Quality-gate applicability for SCRUM-28

This ticket adds only this Markdown governance record. It changes no Java
behavior, architecture boundary, database integration, executable contract,
security control, infrastructure resource, or load-bearing endpoint.

Unit, ArchUnit, integration, contract, security, and load/stress tests are not
applicable to this documentation-only change. No test is created merely to
produce a passing result, and no gate is reported as `PASS`.

## Acceptance result

| Acceptance item | Result |
|---|---|
| Proposed Sprint 1 goal recorded without inferring approval | RECORDED |
| Eight in-scope delivery groups bounded | RECORDED |
| Explicit exclusions and non-goals recorded | RECORDED |
| DEV-only and Learner Lab limits recorded | RECORDED |
| Acceptance gates distinguish requirements from results | RECORDED |
| Closure criteria and unresolved gaps recorded | RECORDED |
| Sprint goal approval | PENDING |
| Sprint-wide implementation and quality evidence | NOT_RUN |
| `docs/` kept read-only and excluded from the tracked deliverable | RECORDED |

## Authoritative local sources

- `docs/00_Gobierno/01_Fuentes_y_orden.md`.
- `docs/00_Gobierno/02_Contradicciones_y_ADR.md`.
- `docs/00_Gobierno/03_Matriz_cumplimiento.md`.
- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`.
- `docs/01_Producto/01_Idea_alcance_y_roles.md`.
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`.
- `docs/06_AWS/04_PoC_y_registro_de_decisiones_bloqueantes.md`.
- `docs/13_Pruebas/01_Plan_de_pruebas_y_calidad.md`.
- `infra/evidence/SCRUM-26-architecture-decisions-and-blockers.md`.
- `infra/evidence/SCRUM-27-sprint-1-requirements-traceability.md`.
- `infra/evidence/SCRUM-30-learner-lab-validation.md`.
- `infra/evidence/SCRUM-37-terraform-state-backend.md`.

The local source files were read only and were not modified.
