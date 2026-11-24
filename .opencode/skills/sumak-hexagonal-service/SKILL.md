---
name: sumak-hexagonal-service
description: Build one SUMAK Java and Gradle service with strict hexagonal, persistence, event, and ArchUnit boundaries
---

## Service boundaries

- Work in one `services/<service>/` module with independent build, artifact, owner, and database.
- `domain/` contains aggregates, value objects, invariants, and domain events; it must not depend on Spring, JPA, brokers, or transport DTOs.
- `application/` contains use cases and input/output ports; orchestration depends inward on domain abstractions.
- `infrastructure/` contains inbound and outbound adapters for GraphQL/gRPC, persistence, messaging, security, and configuration.
- Never share JPA entities, internal DTOs, domain rules, database connections, foreign keys, or migrations across services.

## Communication and data

- Do not add business REST. Use GraphQL at client BFFs, gRPC internally, Kafka for durable facts, RabbitMQ for work, and HTTP only for approved webhooks or technical probes.
- Keep Flyway migrations under the owning service and database. Separate migration and runtime identities; runtime has no DDL permission.
- Persist business state and its Outbox record in one local transaction. Publish only after commit; consumers use Inbox/deduplication and acknowledge only after their local effect commits.
- Apply idempotency keys, expected versions, sanitized errors, and no cross-service SQL.

## ArchUnit gate

Enforce: domain independence; application only depends on domain and ports; infrastructure depends inward; no foreign JPA imports; no business REST controllers; no cyclic package dependencies. A boundary failure blocks completion.
