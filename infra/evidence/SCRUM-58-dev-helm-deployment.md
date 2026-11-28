# SCRUM-58 — DEV Helm deployment operation

## Implemented behavior

The manually dispatched `dev-helm-deploy.yml` workflow validates an explicitly
approved `config-svc` ECR manifest digest, verifies the temporary AWS identity,
connects only to the `sumak-dev` EKS cluster, and deploys the reusable service
chart to namespace `sumak-dev`. The protected `dev` GitHub environment and the
`DEPLOY-DEV` confirmation form the manual authorization boundary.

Deployment uses bounded waits, Helm atomic rollback and failed-install cleanup.
After rollout, the workflow verifies `/health/ready` and `/health/live` through
a temporary local port-forward. Failed health verification restores the recorded
prior revision or removes a first installation. A forward fix requires another
authorized run with a newly approved immutable digest.

## Evidence status

| Item | Status | Evidence required |
| --- | --- | --- |
| Workflow and values static validation | PASS (local static checks only) | Commands and results below |
| DEV account and cluster identity | NOT_RUN | Authorized workflow run |
| Digest existence in approved ECR repository | NOT_RUN | Sanitized workflow summary |
| Helm deployment and bounded rollout | NOT_RUN | Helm and Kubernetes run result |
| Post-deployment health | NOT_RUN | Workflow health-step result |
| Automatic rollback behavior | NOT_RUN | Failed authorized rollout or separately approved exercise |

No cluster execution occurred while implementing this operation. Configuration,
templates, and local rendering are not runtime `PASS` evidence. QA and PROD,
Terraform, IAM, OIDC, AWS resource creation, secrets, and promotion are outside
this ticket.

The workflow references only the protected environment secrets
`SUMAK_DEV_AWS_ACCESS_KEY_ID`, `SUMAK_DEV_AWS_SECRET_ACCESS_KEY`, and
`SUMAK_DEV_AWS_SESSION_TOKEN`; values must never be copied into evidence.

## Static validation

Run without contacting AWS or Kubernetes:

```bash
helm lint infra/helm/service --values config/dev/config-svc-values.yaml
helm template config-svc infra/helm/service \
  --namespace sumak-dev \
  --kube-version 1.36.0 \
  --values config/dev/config-svc-values.yaml
python3 -m unittest tests.test_dev_helm_deploy_workflow \
  tests.test_base_service_helm_chart -v
python3 -m unittest discover -s tests -v
git diff --check
```

Results (2026-11-28): targeted policy/chart tests: **9 passed**; complete
`tests/` discovery: **112 passed**; Helm lint: **1 chart linted, 0 failed**
(non-blocking recommended-icon notice); Helm template completed successfully
for Kubernetes 1.36.0. `git diff --check` completed successfully.
`helm template` parsed and rendered the chart, including the values file. A
separate PyYAML parse was attempted but is unavailable in this environment
(`ModuleNotFoundError: No module named 'yaml'`); it is not represented as a
PASS. The test suite asserts the chart constraint includes 1.32 through 1.37
and rejects 1.31 and 1.38.

Quality-gate matrix for this bounded workflow/chart objective:

| Gate | Status | Reason |
| --- | --- | --- |
| Unit | PASS | 112 static policy and repository tests passed; no runtime cluster behavior inferred |
| Architecture | NOT_RUN | No application/domain dependency changes in scope |
| Integration | NOT_RUN | No authorized AWS/EKS deployment or owning-service database integration |
| Contract | NOT_RUN | No service API/event contract modified |
| Security | NOT_RUN | No security scan/authentication test executed; static workflow checks are not a security gate |
| Load/Stress | NOT_RUN | Deployment runtime is not authorized and no workload is in scope |

DEV AWS/EKS identity, digest lookup, deployment, probes, and rollback remain
**NOT_RUN**; no AWS or Kubernetes deployment command was executed.
