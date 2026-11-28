# Config Service

## Purpose and ownership

`config-svc` owns versioned configuration parameters and effective policy rules in the CFG
bounded context. It is the sole owner of its future `sumak_config` PostgreSQL database.

## Current scope

SCRUM-79 provides only the Java 21 and Spring Boot hexagonal service skeleton:

- pure Java domain;
- application use cases;
- inbound and outbound ports;
- inbound and outbound adapters;
- a minimal Spring Boot entry point; and
- technical health and info actuator endpoints.

Business behavior is intentionally absent. Persistence and Flyway migrations, versioning,
effective-date queries, optimistic locking, events and outbox delivery, GraphQL and gRPC
contracts, authorization, observability, and performance validation belong to later tickets.
No business REST API is exposed.

## Architecture boundaries

Dependencies point inward. The domain must not import Spring, persistence, messaging, AWS, or
transport types. This module must not depend on another service module or share domain and
persistence classes across bounded contexts. Integrations will use versioned contracts.

## Local commands

From the repository root:

```bash
./gradlew :services:config-svc:compileJava
./gradlew :services:config-svc:check
./gradlew :services:config-svc:bootJar
```

The current skeleton requires no database, broker, cloud resource, or credentials.

## Authoritative sources

- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`
- `docs/03_Microservicios/01_Catalogo.md`
- `docs/03_Microservicios/02_Fichas.md`
- `docs/04_Arquitectura/01_Vistas_y_patrones.md`
- `docs/09_DevOps/01_Monorepo_Gradle.md`
- `docs/10_Datos/config-svc.md`
- `docs/11_Contratos/01_Comunicacion_y_eventos.md`

The local `docs/` directory is the read-only source of truth and is not part of this module.
