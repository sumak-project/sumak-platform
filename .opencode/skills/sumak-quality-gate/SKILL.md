---
name: sumak-quality-gate
description: Enforce the six mandatory SUMAK test gates and evidence required before DEV can promote to QA
---

## Six mandatory gates

1. **Unit:** JUnit 5 and AssertJ cover domain invariants, state transitions, idempotency, concurrency versions, and negative cases without AWS.
2. **Architecture:** ArchUnit and linters enforce hexagonal direction, service ownership, no foreign JPA imports, no business REST, and no package cycles.
3. **Integration:** Testcontainers exercise the owning PostgreSQL/PostGIS database, Flyway clean and upgrade paths, transactions, role isolation, Outbox/Inbox, and applicable Kafka/Rabbit dependencies.
4. **Contract:** Compile and validate the affected GraphQL, Protobuf, AsyncAPI, JSON Schema, and approved OpenAPI artifacts; run producer/consumer compatibility and negative error cases.
5. **Security:** Test authentication, issuer/audience/environment isolation, RBAC/ABAC denial, secret and PII redaction, dependency/secret scanning, and unauthorized resource access.
6. **Load/Stress:** Run a reproducible k6 or Gatling workload with documented dataset, concurrency, duration, latency/error/resource observations, and limits. Never extrapolate Learner Lab results to institutional capacity.

## Promotion evidence

For every execution record the commit, command, synthetic dataset, environment/account, OCI digest, DB/schema and contract versions, observed result, logs/metrics, timestamp, and reviewer. Allowed states are `NOT_RUN`, `PASS`, `FAIL`, `BLOCKED_PERMISSIONS`, `BLOCKED_CAPACITY`, `BLOCKED_CONTRACT`, and `WAIVED_WITH_ADR`.

DEV may promote to QA only when all six gates are `PASS`, or an authorized reviewer explicitly accepts a narrowly documented `WAIVED_WITH_ADR`. Any other state blocks promotion. A document, generated test, or screenshot without execution evidence is never a pass.
