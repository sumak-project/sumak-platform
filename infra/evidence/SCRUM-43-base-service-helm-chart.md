# SCRUM-43 base service Helm chart

## Implemented behavior

The reusable chart at `infra/helm/service` renders a Deployment and ClusterIP
Service, with optional ServiceAccount and PodDisruptionBudget resources. It
supports configurable HTTP liveness, readiness, and startup probes; CPU and
memory requests/limits; digest-pinned image references; non-root and
restricted-container security defaults; bounded replica count; termination
grace and rollout settings; and optional scheduling controls.

The DEV values example at `config/dev/base-service-values.yaml` is a
non-runnable placeholder. Replace its repository and digest with an approved
built artifact before any deployment. The chart does not store secret values;
it only accepts references to existing ConfigMaps or Secrets.

## Usage and operational notes

From the repository root:

```bash
helm lint infra/helm/service
helm template example infra/helm/service \
  --namespace sumak-dev \
  --values config/dev/base-service-values.yaml
```

The probe paths and resource defaults are proposed and require service-specific
measurement. Keep liveness shallow; readiness should include only dependencies
critical to serving traffic. Runtime validation requires an application image
with corresponding health endpoints and an authorized target environment.
Namespace selection is not an environment isolation boundary.

Only DEV is active. This change adds no QA/PROD configuration or deployment,
AWS/EKS/Terraform resources, or application runtime. Capacity, security,
availability, and deployment readiness are not claimed.

## Authoritative references

- `docs/09_DevOps/01_Monorepo_Gradle.md`
- `docs/09_DevOps/02_CI_CD_operacion_Jira.md`
- `docs/09_DevOps/03_Pipelines_migraciones_y_despiegues_por_ambiente.md`
- `docs/11_Contratos/01_Comunicacion_y_eventos.md`
- `docs/11_Contratos/02_Operaciones_GraphQL_gRPC.md`
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`

These are local authoritative references; `docs/` was not modified.

## Validation evidence

| Check | Result |
| --- | --- |
| `timeout 30s python3 -m unittest tests.test_base_service_helm_chart -v` | PASS — 4 tests |
| Helm v3.16.4 `helm lint infra/helm/service` | PASS — 1 chart, 0 failed; informational icon recommendation only |
| Helm v3.16.4 `helm template` with DEV values | PASS — rendered to `/tmp/opencode/scrum-43-rendered.yaml`; inspected for all three probes, CPU/memory requests and limits, digest-pinned image, and non-root settings |
| kubeconform v0.6.7, strict, Kubernetes 1.31.0 | PASS — 2 resources valid; 0 invalid, errors, or skipped |
| `git diff --check` | PASS |
| Secret/latest scan | PASS — bounded heuristic scan of changed source/evidence files found no credential-like literals or `latest`/tag fields; dedicated secret-scanning tool unavailable, so formal security scanning remains NOT_RUN |
| kind/k3d runtime | NOT_RUN — no deployable application image or health endpoint exists |
| Architecture / Integration / Contract / formal Security / Load-Stress gates | NOT_RUN — not established by the chart-focused static checks; no contract changes or runtime workload |
| Full repository checks | NOT_RUN — outside this bounded chart validation |

Helm and kubeconform were temporarily downloaded to `/tmp/opencode`; the
Helm distribution and kubeconform release checksums matched their published
checksums. No temporary binaries or rendered files are part of this change.
