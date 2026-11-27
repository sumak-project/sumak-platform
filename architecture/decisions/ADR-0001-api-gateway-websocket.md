# ADR-0001: Retain the ALB-hosted Realtime Gateway Baseline

- **Status:** Accepted for the current MVP baseline
- **Decision date:** 2026-11-27
- **Jira:** SCRUM-44
- **Decision owner:** SUMAK platform architecture
- **Runtime evidence:** NOT_RUN

## Context

SUMAK needs authenticated WebSocket Secure (WSS) delivery for notification and
aggregated process-status updates. The requirements mention Amazon API Gateway
WebSocket API as a reference option, while the latest MVP direction defines a
Java `realtime-gateway`, private Redis connection registry, and Application Load
Balancer (ALB) as the baseline.

Amazon API Gateway must not be confused with, or automatically replace, the
logical gateway deployed in EKS. Adopting it requires an explicit decision based
on permissions, quotas, cost, operational fit, security, and measured capacity.

The current DEV environment has no authorized DNS/hosted-zone/ACM path for this
evaluation. SCRUM-136, which owns ALB runtime validation for TLS and WSS, is not
complete. No AWS apply or proof-of-concept authorization was granted for this
ticket.

## Decision

Retain the Java `realtime-gateway` with a private Redis registry behind the ALB
as the MVP baseline. Retain the logical EKS gateway and its GraphQL/BFF role.

Amazon API Gateway WebSocket API remains a **PROPOSED optional complement** that
may be reconsidered through a separately authorized DEV proof of concept after
SCRUM-136 supplies the required runtime prerequisites and evidence. It is not
approved as a replacement for either gateway.

This decision resolves the apparent tension in RTO-NET-06 by applying the
documented source precedence: its managed WebSocket reference is conditional,
while the later explicit MVP baseline remains authoritative until a measured
PoC supports a new ADR.

## Scope and boundaries

- WSS carries notification, inbox, and aggregated process-status updates only.
- Business commands, voting selections, ballots, participation streams, PII,
  access tokens, and reusable credentials are prohibited on the socket.
- Client-facing business interactions remain GraphQL; internal synchronous
  integration remains gRPC. This ADR introduces no business REST surface.
- The connection flow uses OIDC-backed, opaque, single-use realtime tickets.
  Ticket material is hashed in private Redis and is not placed in a URL as a
  JWT.
- Subscription authorization must not exceed the authenticated user's existing
  permissions. Session expiry, revocation, reconnect, and GraphQL resync remain
  mandatory.
- A WSS outage must not block core operations; inbox/resync and approved push
  paths provide fallback.
- This decision applies to DEV architecture only. It authorizes no QA or
  production resource, deployment, or migration.

## Options considered

### 1. Java realtime gateway, private Redis, and ALB — selected

**Advantages**

- Matches the latest explicit MVP and contract direction.
- Reuses the planned EKS and ALB operational boundary.
- Keeps connection-ticket validation, authorization, backpressure, and resync
  behavior close to the versioned SUMAK contracts.
- Avoids adding an unproven managed-service dependency.

**Trade-offs**

- SUMAK owns scaling, connection lifecycle, patching, and runtime operations.
- ALB idle-timeout, draining, TLS/WSS, health, and origin-protection behavior
  still require measured DEV validation under SCRUM-136.

### 2. Amazon API Gateway WebSocket API as a complement — deferred

**Potential advantages**

- Managed connection entry point and connection lifecycle primitives.
- Independent scaling boundary that might reduce gateway pod connection load.

**Unverified concerns**

- Learner Lab permissions, service availability, quotas, authorizer support,
  integration shape, and `iam:PassRole` constraints.
- Added routing, observability, failure-mode, and cost complexity beside the
  existing ALB and logical gateways.
- Secure mapping between opaque connection identifiers, private Redis state,
  revocation, fan-out scopes, and GraphQL resync.
- Cost behavior for connection minutes and messages under realistic traffic.

These items are **PENDING** and cannot be treated as approval.

### 3. Amazon API Gateway as a general gateway replacement — rejected

This would conflict with the current logical gateway and GraphQL/gRPC split,
expand the ticket into a platform migration, and risk introducing unauthorized
business REST. No evidence supports that change.

## Security and network consequences

- TLS is mandatory for all WebSocket connections.
- Connection identifiers are opaque and are never credentials.
- Authentication and authorization are required at connection and subscription
  boundaries; rate limits, idle timeouts, revocation, heartbeat, backpressure,
  and abuse controls require implementation and validation.
- The ALB-to-gateway route must remain restricted by security groups.
- No new IAM role, cross-account assumption, hosted zone, domain, or
  environment is authorized by this ADR.
- Sanitized synthetic data is required for future validation; real personal or
  voting data is prohibited.

## Learner Lab and capacity assessment

The baseline must remain within Learner Lab limits, including the existing-role
model and restricted compute, storage, and service quotas. A managed WebSocket
PoC must first verify API availability, allowed API actions, quotas, authorizer
integration, and role-passing behavior without creating unauthorized IAM
resources.

The target of 5,000 concurrent authenticated WebSocket connections belongs to
an authorized `staging-perf` environment outside Learner Lab. It is an
**UNPROVEN TARGET**, not evidence of current capacity. This ADR makes no
availability, security, performance, cost, or production-readiness claim.

## Required evidence before reconsideration

A follow-up decision may reconsider the managed service only after all of the
following are available:

1. SCRUM-136 has validated or precisely blocked the DEV TLS/WSS prerequisites.
2. AWS mutation and PoC execution have separate explicit authorization.
3. The PoC records date, account, region, role, API action, IaC commit, result,
   sanitized errors/captures, observed quotas, duration, and cost.
4. Synthetic tests cover authorized `$connect`, subscription/message delivery,
   revocation or expiry behavior, `$disconnect`, reconnect/resync, and cleanup.
5. The comparison covers failure isolation, observability, security controls,
   operational ownership, quotas, and representative cost.

Permitted blocker labels include `BLOCKED_AWS_PERMISSION`, `BLOCKED_QUOTA`,
`BLOCKED_SECURITY`, and `BLOCKED_EXTERNAL_DEPENDENCY`.

## Validation record

| Evidence | Status | Notes |
|---|---|---|
| Architecture and contract comparison | REVIEWED | Sources below were compared using the documented precedence. |
| Managed WebSocket API PoC | NOT_RUN | No authorized DNS/hosted-zone/ACM path, SCRUM-136 is incomplete, and AWS apply was not authorized. |
| ALB TLS/WSS runtime behavior | NOT_RUN | Owned by SCRUM-136. |
| Authentication and authorization runtime checks | NOT_RUN | Requires an authorized synthetic PoC. |
| Quota and 5,000-connection capacity measurement | NOT_RUN | Requires authorized `staging-perf` outside Learner Lab. |
| Cost measurement | NOT_RUN | No managed WebSocket resource was provisioned. |

## Authoritative sources

- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`
- `docs/00_Gobierno/02_Contradicciones_y_ADR.md`
- `docs/05_Tecnologias/02_Fichas_de_decision_por_tecnologia.md`
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`
- `docs/06_AWS/02_Servicios_y_PoC.md`
- `docs/06_AWS/03_Mapa_de_recursos_y_dependencias_por_cuenta.md`
- `docs/06_AWS/04_PoC_y_registro_de_decisiones_bloqueantes.md`
- `docs/11_Contratos/01_Comunicacion_y_eventos.md`
- `docs/07_Integraciones/03_Notificaciones_WebSocket_y_reconexion.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_NET.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_REALTIME.md`
- `docs/01_Producto/Requisitos_Trazados/RF_NOTIF.md`
- `docs/01_Producto/Requisitos_Trazados/RNF_SEC.md`
- `docs/01_Producto/Requisitos_Trazados/RNF_PERF.md`

The ignored `docs/` tree remains the read-only source of truth. This tracked ADR
records the bounded repository decision and does not modify those sources.
