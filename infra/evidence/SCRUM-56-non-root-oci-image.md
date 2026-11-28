# SCRUM-56: Non-root OCI image evidence

## Implemented behavior

`config-svc` now has a multi-stage OCI build using digest-pinned Eclipse Temurin 21 Alpine builder and JRE images. The runtime runs as UID/GID `10001:10001`, includes the packaged application only, declares a Docker health check, and exposes live, ready, and startup health endpoints. Actuator health details are hidden. A static packaging contract test covers the image user, health check, and probe configuration.

## Setup and operational notes

- Build from the repository root with `docker build -f services/config-svc/Dockerfile -t sumak/config-svc:scrum-56 .`.
- For hardened local execution, use a read-only root filesystem, writable `/tmp` tmpfs, drop all capabilities, and enable `no-new-privileges`.
- The Docker health check calls `/health/live`, `/health/ready`, and `/health/startup`. Helm rendering must specify a Kubernetes version supported by the chart; local client defaults may be newer than its bound.
- Builder: `eclipse-temurin:21-jdk-alpine@sha256:c07bb82e004a166b5d3d63b84ad70e2e822f228505e2e0c0b8dfdc2890d22f13`. Runtime: `eclipse-temurin:21-jre-alpine@sha256:5d7689f47d670aca766b9503a70bccc2d73b4eb9221ae8f714ae958313c4ce70`.

## Validation evidence

Tool versions: Docker 29.10.1, Java 21.0.13.1, Gradle 8.14.3, Trivy 0.76.2. Helm client rendering used Kubernetes version `1.32.0`.

| Command/check | Result |
| --- | --- |
| `docker build -f services/config-svc/Dockerfile -t sumak/config-svc:scrum-56 .` | PASS |
| Hardened `docker run` (read-only root, `/tmp` tmpfs, `--cap-drop ALL`, `no-new-privileges`) | PASS |
| `docker inspect` runtime user and health | PASS: `10001:10001`; `healthy` |
| `/health/live`, `/health/ready`, `/health/startup` | PASS: each returned `{"status":"UP"}` |
| Runtime identity/tool checks | PASS: UID/GID 10001; no Gradle or `javac` |
| `trivy image --scanners vuln,secret --severity HIGH,CRITICAL --exit-code 1 --ignore-unfixed sumak/config-svc:scrum-56` | PASS after Spring Boot 4.2.0/WebFlux update: zero HIGH/CRITICAL findings reported for Alpine and the JAR. Trivy's summary showed `-` for secrets (no supported secret target reported there); this is not a claim of a comprehensive secret scan. |
| `./gradlew check --no-daemon` | PASS: 106 tasks (28 executed, 78 up-to-date) |
| `python3 -m unittest discover -s tests -v` | PASS: 88 tests |
| `helm lint infra/helm/service` | PASS (icon recommendation only) |
| Initial Helm template without explicit Kubernetes version | FAILED: local client default `1.37` is outside the chart's bound. |
| `helm template config-svc infra/helm/service --kube-version 1.32.0 --set image.repository=sumak/config-svc --set image.digest=sha256:f79a6503fa69c0637562951df36424876a6502f9d9bd1bd9cc980ec956ec8ad2` | PASS: rendered configured image reference, UID 10001, and all three probes. The supplied value is the local Docker image ID encoded in chart digest syntax for template validation only; it is not a registry manifest/digest or publishable artifact. |
| `git diff --check` | PASS |

Built local image ID: `sha256:f79a6503fa69c0637562951df36424876a6502f9d9bd1bd9cc980ec956ec8ad2`; size: `369481538` bytes. This is a local image ID, not a registry digest. The CycloneDX 1.7 SBOM at `/tmp/opencode/SCRUM-56-config-svc-sbom.cdx.json` contains 145 components; it was generated locally and is intentionally not tracked.

## Authoritative references

- `docs/09_DevOps/02_CI_CD_operacion_Jira.md`
- `docs/09_DevOps/03_Pipelines_migraciones_y_despiegues_por_ambiente.md`
- `docs/05_Tecnologias/01_Inventario_y_decisiones.md`
- `docs/11_Contratos/02_Operaciones_GraphQL_gRPC.md`
- `docs/11_Contratos/04_Estandares_y_fallos_de_contratos.md`
- `docs/13_Pruebas/01_Plan_de_pruebas_y_calidad.md`

## Limitations and exclusions

- No ECR push, pull, or registry-digest recovery; that is SCRUM-54 scope.
- No Helm deployment or cluster-runtime validation; that is SCRUM-58 scope.
- No QA/PROD or AWS claims, and no capacity or compliance claims.
- Trivy's `-` secret summary is not evidence that all secret types or targets were scanned.

## Commit and PR

- Commit: pending.
- Pull request: pending (target `dev`).
