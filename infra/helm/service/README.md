# SUMAK base service Helm chart

Reusable base chart for stateless SUMAK services. Platform/DevOps owns this
chart; each service will supply its immutable image digest and measured runtime
settings when that service is implemented.

## Status and boundaries

- Chart authoring is implemented for SCRUM-43.
- Probe paths are a proposed technical contract, not deployed runtime evidence.
- Resource defaults are provisional and require measurement under Learner Lab
  limits before any capacity claim.
- Application images, health endpoints, EKS installation, and kind/k3d runtime
  checks are not part of this chart and remain `NOT_RUN`.
- Only DEV is active. QA and PROD deployment/configuration are intentionally
  excluded until their required gates exist.
- Namespace selection does not provide environment isolation. Accounts, VPCs,
  credentials, data, and keys provide that boundary.

## Render locally

Helm 3 is required:

```bash
helm lint infra/helm/service
helm template example infra/helm/service \
  --namespace sumak-dev \
  --values config/dev/base-service-values.yaml
```

The default image is deliberately non-runnable. Replace both
`image.repository` and `image.digest`; tags, including `latest`, are unsupported.

## Values contract

- `image.repository` and `image.digest`: immutable workload image reference.
- `config.existingConfigMap` / `config.existingSecret`: references only; this
  chart never stores secret values.
- `resources.requests` / `resources.limits`: required CPU and memory budgets.
- `probes.*`: configurable HTTP liveness, readiness, and startup checks.
- `replicaCount`: bounded to 1–3 to protect the provisional Learner Lab budget.
- `serviceAccount.create`: opt-in ServiceAccount with token mounting disabled by
  default.
- `podDisruptionBudget` and `topologySpreadConstraints`: optional scheduling
  controls.

The default liveness probe must remain shallow. Readiness may check only
dependencies that are critical to serving traffic.

## Authoritative references

- `docs/09_DevOps/01_Monorepo_Gradle.md`
- `docs/09_DevOps/02_CI_CD_operacion_Jira.md`
- `docs/09_DevOps/03_Pipelines_migraciones_y_despiegues_por_ambiente.md`
- `docs/11_Contratos/01_Comunicacion_y_eventos.md`
- `docs/11_Contratos/02_Operaciones_GraphQL_gRPC.md`
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`
