# SCRUM-39 — DEV teardown and recovery runbook

## Purpose and boundaries

This runbook provides a controlled, granular procedure for tearing down and
recovering approved DEV resources. It is operational guidance, not evidence
that any AWS operation has occurred. It covers only the two DEV accounts and
their explicitly owned resources. It does not authorize teardown, state
mutation, or deployment.

## Inventory and ownership

| Account | Profile / role | Region | Ownership boundary |
|---|---|---|---|
| `sumak-dev` | `sumak-dev` / temporary `LabRole` | `us-east-1` | Primary DEV resources declared beneath `infra/accounts/sumak-dev/us-east-1/dev/`; the map records the account identifier only as `****9751`. |
| `sumak-dev-integration` | `sumak-dev-integration` / temporary `LabRole` | `us-east-1` | Integration-account resources only. The account identifier is `PENDING_ASSIGNMENT`; no owned-resource inventory or deployed resource set is implied by this entry. Establish and review its inventory before any operation. |

These records are the tracked inventory baseline, not proof of live account
contents. Reconcile each account's current inventory, Terraform state, and
ownership before acting. If caller identity, region, ownership, state backend,
or inventory is uncertain or mismatched, stop: mark the target
`TARGET_UNVERIFIED` and do not proceed. Keep state and recovery material
separate per account. Never copy, point, or reuse one account's state, backend,
credentials, or resource identifiers in the other account. No PROD account,
QA account, or cross-account resource is in scope.

## Prerequisites and freeze

Before any approved teardown:

1. Obtain explicit change approval, a named operator, a maintenance window,
   and a rollback/recovery owner. Confirm the target is DEV and the exact
   account, region, and resource set.
2. Freeze deployments, Terraform writers, scheduled jobs, and other resource
   changes for the target. Confirm no active operation or state lock remains;
   never remove a lock merely to proceed.
3. Verify temporary credentials and caller identity through the approved
   organizational process, then compare the account against the reviewed
   account map and independently verified account inventory. Do not record
   credentials or sensitive identity output in this runbook or evidence.
4. Review ownership and dependencies, including DNS/certificates, network,
   application consumers, data retention, and recovery requirements. Identify
   resources not represented in Terraform state and explicitly exclude them
   unless separately approved.
5. Preserve a protected, access-controlled copy of each account's state and
   relevant object versions, plans, and evidence. Verify recovery prerequisites
   before any destructive change. Do not place state, secrets, or credentials
   in Git.
6. Inspect a fresh, reviewed plan for the exact account and bounded target.
   Any unplanned replacement, cross-account action, protected-resource action,
   or unclear dependency is a stop condition. This runbook intentionally
   contains no executable cloud or Terraform teardown commands.

Learner Lab is temporary and constrained: capacity is at most **9 EC2
instances per account** and **32 vCPUs per region**. RDS support/quotas, public
IPv4 availability, and session duration can vary. Stopped RDS instances may
automatically restart after 7 days; account for this in freeze, cost, and
monitoring plans. Confirm current lab policy and capacity before recovery.
Restarting EC2 can change its public IP, and a public IP is never a stable
endpoint. Public IP allocation or reassociation may be restricted. Prior
success does not establish current availability or permission.

## Pre-freeze capture and resource-class inventory

Before the freeze, capture timestamped, access-controlled manifests and
cryptographic hashes for in-scope configuration, deployment artifacts, and
recoverable data references. Capture a cost snapshot for each account/region.
Do not put secrets, state contents, or sensitive data in Git. Record missing
captures as `NOT_RUN` or a blocker.

Reconcile this complete resource-class checklist against live inventory,
ownership, Terraform state, and preservation requirements. Listing a class
does not imply it exists. Record each as `ABSENT`, `PRESENT`, `NOT_RUN`, or
`TARGET_UNVERIFIED` with evidence. Architecture specifies 19 independent
PostgreSQL databases and 3 DynamoDB tables; establish actual per-service
inventory and ownership rather than assuming deployment.

- [ ] PostgreSQL: all 19 independent databases and service/account owners.
- [ ] DynamoDB: all 3 tables and owners.
- [ ] Isolated urna/anonymous-ballot, voter-eligibility, and tally stores and
  services; never join or co-locate these domains.
- [ ] S3 media, web/static assets, audit, data lake, and Terraform state,
  including required object versions and retention.
- [ ] Kafka topics and retained/replayable events.
- [ ] RabbitMQ queues, bindings, and work/dead-letter data.
- [ ] OpenSearch indexes, mappings, and snapshots.
- [ ] Redis instances, key/TTL requirements, and reconstructibility.
- [ ] Keycloak realms and Active Directory (AD) configuration/ownership.
- [ ] n8n workflows, secret references (not values), and execution history.
- [ ] Besu nodes, chain data, genesis/network configuration, validators, peers.
- [ ] IA/ETL workloads, schedules, inputs/outputs, checkpoints, lineage.
- [ ] EKS clusters and compute (EC2, workloads, volumes, images, capacity).
- [ ] Observability: metrics, logs, traces, alerts, dashboards, retention.
- [ ] IaC: per-account Terraform state/backends, locks, versions, modules.

Resolve concrete names and owners from the authoritative service/data
catalogue. If ownership is uncertain, do not touch the resource.

## Ordered safe teardown

Proceed only for individually approved resources and in dependency order.
Record each action and resulting identifier; pause on any discrepancy.

1. Announce the freeze and verify application owners have stopped or drained
   DEV workloads and background processing.
2. Capture per-account inventory, Terraform state snapshot/version references,
   reviewed plan, dependency map, and required data backups. Confirm restore
   tests or explicitly record them as `NOT_RUN`.
3. Fence Besu before removing any network or compute dependency: stop new
   validators/peers and transaction submission, coordinate the consortium
   operator, preserve chain data and genesis/network configuration, and record
   the agreed final block/height and peer set. Confirm independent confirmation
   that the network is fenced. If this cannot be verified, stop before touching
   Besu, its storage, or supporting networking. Never delete chain data as a
   routine cleanup step.
4. Remove only approved stateless application/workload resources, after their
   owners confirm shutdown and any required artifacts/logs are preserved.
5. Remove approved ingress and edge resources only after consumers are
   detached and DNS/TLS dependencies and recovery requirements are recorded.
6. Remove approved compute and integration components, respecting Learner Lab
   limits and data dependencies. Do not infer that an account is empty from
   Terraform state alone.
7. Remove approved network components from dependents toward foundations,
   only after proving they are unused. Preserve shared or externally owned
   components unless their owner separately approves removal.
8. Handle state backends last, and only under a separate explicit approval
   after all managed resources are reconciled and recovery copies verified.
   Never remove a state bucket/object, lock, or version history as ordinary
   teardown.
9. Reconcile actual inventory against the approved target and each account's
   state. Report residual, unmanaged, or failed resources; do not silently
   broaden the teardown to clear them.

## Explicit preservation list

Unless a separate, explicit retention/destruction decision authorizes
otherwise, preserve:

- Terraform state backends, current state, lock evidence, and version history;
- Besu chain data, genesis/network configuration, and final-height evidence;
- required application/database data and approved backups;
- ECR images by immutable digest and required build provenance;
- logs, audit records, security evidence, and incident/change records;
- DNS names, certificates, and configuration needed for safe recovery;
- shared/network resources whose ownership or consumers are not confirmed.

Preservation is not a claim that these artifacts currently exist or have been
backed up. Record missing artifacts as blockers; do not claim recoverability
without verified copies.

## Granular recovery and verification

Recover only the failed component or dependency chain, not the whole account by
default. Keep the two account procedures and evidence separate.

1. Stop changes and establish the incident/change owner. Preserve incident
   evidence, capture current state/manifests/hashes and a fresh cost snapshot.
   Re-verify account, region, target, ownership, and Learner Lab capacity. If
   uncertain, record `TARGET_UNVERIFIED` and stop.
2. Identify the last known-good state and resource versions. Preserve current
   state before recovery; select state/object versions only with review and
   approval. Use the account's own backend and credentials; never cross-reuse.
3. For a single PostgreSQL database, restore its selected snapshot to an
   isolated recovery instance. Dump only the approved target database and
   restore only that database into its intended target. Verify schema,
   grants/roles, row counts, domain invariants, and Flyway migration sequence.
   Reconcile outbox/inbox records and Kafka/S3 effects using an agreed
   watermark before reconnecting consumers. Never overwrite neighboring
   databases or another service owner's data. A cluster snapshot is not a
   granular restore; it is only a source for this isolated, target-database-only
   process.
4. Restore other data/state prerequisites, then foundational networking,
   dependencies, workloads, and finally ingress/DNS. Follow the relevant
   component's reviewed procedure; this runbook does not authorize or prescribe
   apply/destroy execution.
5. For Besu recovery, retain the fence while restoring chain data and
   configuration. Verify chain identity, expected final height, peer/validator
   membership, and operator agreement before controlled un-fencing. If
   consistency is uncertain, keep it fenced and escalate.
6. Verify each recovered component independently: expected account and region,
   ownership, state/resource reconciliation, health/readiness, dependency
   connectivity, data integrity, and access boundaries. Record evidence
   references and timestamp without exposing credentials or sensitive output.
7. Run functional and security smoke checks, including access-denial and data
   isolation checks. Recovery never automatically reopens voting; never join
   identity data with anonymous ballot data.
8. Validate Learner Lab limits again before adding EC2 capacity or requesting
   RDS/public-IP resources. A quota, service-policy, session, or IP limitation
   is a blocker; do not substitute another account or environment.
9. Obtain component-owner verification and explicit promotion/release approval
   before lifting the freeze incrementally. Unresolved checks are `NOT_RUN`,
   `PENDING`, or `TARGET_UNVERIFIED`, never success.

RPO/RTO remain `TARGET_UNVERIFIED` unless supported by an approved measured
exercise, recorded as `LAB_MEASUREMENT` with scope, conditions, timestamp, and
result. A lab measurement is not a production commitment.

## Evidence record

Create one record per account and recovery/teardown window. Use only
`PASS`/`FAIL` when supported by direct, timestamped evidence; otherwise use
`NOT_RUN`, `PENDING`, `BLOCKED`, or `TARGET_UNVERIFIED`.

| Field | Record |
|---|---|
| Ticket / approved change | |
| Operator and approver | |
| UTC window | |
| Environment / account name | |
| Account verification reference (redacted) | |
| Region and bounded resource scope | |
| Inventory and ownership source/revision | |
| Freeze and active-writer check | |
| Pre-freeze manifests/hashes and capture time | |
| Cost: measured consumption, official rate source, period | |
| State snapshot/version reference (protected location; no state in Git) | |
| Resource-class inventory status and evidence | |
| Besu fence status / final height / operator evidence, if applicable | |
| Learner Lab limits (≤9 EC2/account; ≤32 vCPU/region; RDS 7-day restart; public-IP volatility) | |
| Reviewed plan / approval reference | |
| Isolated database restore and validation/reconciliation evidence | |
| Per-step result and timestamp | |
| Preservation and backup verification | |
| Recovery/component verification evidence | |
| Functional/security smoke and promotion approval | |
| RPO/RTO (`TARGET_UNVERIFIED` or `LAB_MEASUREMENT`) | |
| Vote remains closed; identity/ballot separation confirmed | |
| Checks not run and reason | |
| Residual resources, blockers, and follow-up owner | |
| Freeze release approval | |

No runtime operation is asserted by this template. Until direct evidence is
attached, checks are `NOT_RUN`; an unconfirmed account or resource target is
`TARGET_UNVERIFIED`, not a verified target or a pass.

## Authoritative and tracked references

- `infra/accounts-map.yaml` — account names, groups, regions, roles, and
  assignment status.
- `infra/accounts/sumak-dev/us-east-1/dev/` — tracked primary DEV Terraform
  ownership boundaries; it is not a complete live-resource inventory.
- `infra/accounts/sumak-dev/us-east-1/dev/state-backend/README.md` — primary
  DEV state backend safety and recovery guidance.
- `infra/evidence/SCRUM-29-environment-evidence-checklist.md` and
  `infra/evidence/SCRUM-30-learner-lab-validation.md` — environment evidence
  and Learner Lab constraints.
- `infra/evidence/SCRUM-37-terraform-state-backend.md` and
  `infra/evidence/SCRUM-38-ecr-repositories.md` — tracked state and artifact
  evidence.
- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md` — source authority
  and verified-source limitations.
- `docs/03_Microservicios/01_Catalogo.md` — service boundaries and ownership.
- `docs/10_Datos/` — per-service persistence ownership and fields; consult the
  exact database owner's document.
- `docs/11_Contratos/` — cross-service protocols and event/data boundaries.
- `docs/09_DevOps/` — environment, infrastructure, operations, and recovery
  source material; consult the exact applicable document.
- `docs/01_Producto/Requisitos_Trazados/` — applicable requirements/status.
- `AGENTS.md` — DEV-only boundary, evidence language, and prohibition on
  editing ignored `docs/`.
- The approved ticket/change record must identify exact authoritative
  documents for Learner Lab, Besu, database recovery, RPO/RTO, cost, and
  teardown. Do not fabricate requirements or infer missing filenames;
  unresolved source references are a blocker. `docs/` remains read-only.
