# SCRUM-48 Terraform CI quality checks

## Implemented behavior

Pull requests targeting `dev` run a blocking Terraform job before merge. The
job checks formatting, initializes every account root without a backend,
validates each root, scans Terraform configuration for high or critical
security/policy findings, verifies the temporary AWS identity, and creates
reviewable plans for the foundational `network` and `network-boundaries` roots
against their configured encrypted remote state.

The plan step fails closed unless all temporary `sumak-dev` credential secrets
and the expected account ID repository variable are present and a live
`aws sts get-caller-identity` result matches that account. Credentials, state,
and plan files are not committed. Credentials are exposed only to the plan
step, written to a runner-temporary named profile for the existing backend and
provider configuration, and deleted on step exit. Plan artifacts are retained
for one day.

Required GitHub configuration:

- Secrets: `SUMAK_DEV_AWS_ACCESS_KEY_ID`,
  `SUMAK_DEV_AWS_SECRET_ACCESS_KEY`, and `SUMAK_DEV_AWS_SESSION_TOKEN`.
- Repository variable: `SUMAK_DEV_AWS_ACCOUNT_ID`.
- The `Terraform quality gates` job must be configured as a required branch
  protection check outside this repository.

Learner Lab sessions are temporary. An expired or missing session is
`BLOCKED_PERMISSIONS`, not a successful plan. Refresh it through the approved
account access process; never replace it with long-lived credentials.

Parameterized roots such as bastion, EKS, and PostgreSQL remain covered by
format, backend-free validation, tests, and security scanning. They are not
planned with invented values: their live inventory, role, subnet, and
owner-security-group inputs must come from an authorized deployment workflow.

## Bounded scope and exclusions

- This change adds CI checks only. It does not apply, deploy, destroy, or change
  Terraform-managed resources.
- It does not add IAM roles, cross-account access, QA/PROD configuration, drift
  detection, or a separate infrastructure repository.
- A successful configuration scan or plan is evidence for the reviewed commit,
  not a claim of production readiness, legal compliance, measured capacity, or
  AWS availability.
- Any future `terraform apply` requires separate human approval and fresh
  account, quota, inventory, and plan verification.

## Validation evidence

| Check | Result |
|---|---|
| `terraform fmt -check -recursive infra` | `PASS` |
| Backend-free initialization and validation of all 8 account roots | `PASS`; `hashicorp/aws` 6.74.0 |
| Trivy security/policy scan | Initial CI run `FAIL`; narrow reviewed exceptions added for the intentional public ALB, public-ingress subnets, and EKS >=1.28 default envelope encryption; rerun pending |
| STS identity and account match | `NOT_RUN`; requires temporary CI credentials |
| Reviewed Terraform plans | `BLOCKED_PERMISSIONS` locally; no temporary session was supplied |
| Workflow YAML parse | `PASS` |
| `python3 -m unittest discover -s tests -v` | `PASS` (78 tests) |
| `git diff --check` | `PASS` |

No Terraform apply was run or authorized by this ticket.

## Authoritative references

- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_IAC.md` (`RTO-IAC-05` and
  `RTO-IAC-06`)
- `docs/09_DevOps/02_CI_CD_operacion_Jira.md`
- `docs/09_DevOps/03_Pipelines_migraciones_y_despiegues_por_ambiente.md`
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`
- `infra/accounts-map.yaml`

Ignored `docs/` remains read-only and was not modified.
