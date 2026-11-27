# SCRUM-45 logical Spring API gateway

## Implemented behavior

`platform/api-gateway` is a Java 21 Spring Cloud Gateway component with no
business routes. Spring Actuator exposes only the contract-aligned technical
operations `/health`, `/health/live`, `/health/ready`, `/health/startup`, and
`/version`. Those operations are unauthenticated for platform probes; every
other request is denied until a reviewed route and authentication policy are
implemented.

`config/dev/api-gateway-values.yaml` integrates the component with the reusable
service Helm chart as a private ClusterIP workload. Probe paths match the
application endpoints and the ALB health-path convention. Resource settings are
bounded but remain proposed pending measurement. The image repository and
digest are explicit non-runnable placeholders, not deployment evidence.
The reusable ALB module and DEV root use `/health/ready` as the target-group
health path, so application, Helm, and Terraform configuration agree.

## Operational constraints

- DEV is the only active environment.
- No business REST/Swagger route, persistence ownership, managed API Gateway,
  ECS fallback, public Service, AWS mutation, or QA/PROD configuration is added.
- Replace the image placeholders with an approved immutable artifact before an
  authorized deployment.
- SCRUM-35 DNS/ACM, SCRUM-36 runtime ALB evidence, and SCRUM-46 EKS control
  plane remain prerequisites. ALB target health, TLS, WSS, rollback, and
  deployment checks are therefore `NOT_RUN`/blocked rather than `PASS`.
- The previously proposed ALB target transport (`HTTPS` on `8443`) is not
  changed or claimed compatible with the current HTTP container port. It needs
  an authorized transport decision and runtime evidence before target
  registration; this ticket does not weaken that boundary to manufacture a
  runnable deployment.

## Authoritative references

- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_NET.md`
- `docs/03_Microservicios/01_Catalogo.md`
- `docs/05_Tecnologias/01_Inventario_y_decisiones.md`
- `docs/09_DevOps/03_Pipelines_migraciones_y_despiegues_por_ambiente.md`
- `docs/11_Contratos/02_Operaciones_GraphQL_gRPC.md`
- `docs/13_Pruebas/01_Plan_de_pruebas_y_calidad.md`

These local sources were read but not modified.

## Validation evidence

| Check | Result |
| --- | --- |
| `./gradlew check` | PASS — full configured Gradle check, including gateway unit, contract/security, and ArchUnit tests |
| `python3 -m unittest discover -s tests -v` | PASS — full repository Python test discovery |
| Helm v3.16.4 `lint` and `template` with gateway DEV values | PASS — chart linted and rendered to `/tmp/opencode/scrum-45-rendered.yaml` |
| kubeconform v0.6.7, strict, Kubernetes 1.31.0 | PASS — rendered resources validated |
| `terraform fmt -check` and `terraform validate` for the ALB module and DEV root | PASS — AWS provider v6.74.0 |
| `git diff --check` | PASS |
| Bounded credential and mutable-image heuristic | PASS — no credential-like assignment or `latest` image found; formal secret scanning remains `NOT_RUN` |
| EKS deployment and ALB target registration | `BLOCKED_EXTERNAL_DEPENDENCY` — SCRUM-46 control plane and an approved immutable image are unavailable |
| ALB target transport/port compatibility | `NOT_RUN` — existing target is HTTPS:8443 while this workload is HTTP:8080; an authorized transport decision is required |
| DNS, TLS, target health, WSS, rollback, and teardown | `BLOCKED_EXTERNAL_DEPENDENCY` — SCRUM-35/36/46 prerequisites remain unavailable |
| Integration and load/stress gates | `NOT_RUN` — no authorized deployable runtime exists |

Helm and kubeconform were downloaded only to `/tmp/opencode`; their published
SHA-256 checksums matched. Static checks do not establish deployment readiness.
