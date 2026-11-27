# SCRUM-40 — DEV EKS managed node group evidence

- Scope: reusable managed-node-group module and DEV-only Terraform root.
- Implementation status: `IMPLEMENTED_PLAN_ONLY`.
- Infrastructure plan/apply: `NOT_RUN`.
- Runtime node, Pod health, rollout, quota, teardown, and cost checks: `NOT_RUN`.
- External dependency: `BLOCKED_EXTERNAL_DEPENDENCY` pending the SCRUM-46 EKS
  control plane and authorized cluster and node-role inputs.

## Implemented behavior

- Exactly three `t3.large` On-Demand managed nodes with fixed minimum, desired,
  and maximum size of three.
- Three distinct existing private subnets and availability zones are required.
- A launch template enforces encrypted `gp2` root volumes bounded to 100 GiB,
  IMDSv2, and detailed monitoring.
- The EKS cluster and Learner Lab node role are external inputs; this scope
  creates no cluster, IAM role, IRSA, VPC, subnet, workload, or other
  environment.
- The DEV root uses the same-account encrypted S3 backend with native locking.

## Quota and rollout boundaries

- Declared steady-state capacity is three instances and six vCPUs, inside the
  DEV planning cap of five instances and the Learner Lab ceilings of nine
  running EC2 instances per account and 32 EC2 vCPUs per region.
- The autoscaling maximum is fixed at three. Before any authorized plan or
  apply, the operator must verify current account-wide EC2 use and stop if the
  proposed capacity or rollout could cross the DEV or Learner Lab ceiling.
- Account-wide EC2 count is not emitted as a native CloudWatch metric by this
  stack. No nonfunctional alarm or custom metric without a publisher is
  declared; alert-at-seven runtime monitoring remains `NOT_RUN` and must be
  supplied by an authorized account-level inventory mechanism.

## Validation evidence

- `terraform fmt -recursive infra`: `PASS`.
- `terraform init -backend=false && terraform validate` in the DEV EKS root:
  `PASS` with Terraform provider `hashicorp/aws` 6.74.0.
- `python3 -m unittest tests.test_dev_eks_managed_node_group_boundaries -v`:
  `PASS` (5 tests).
- `python3 -m unittest discover -s tests -v`: `PASS` (46 tests).
- `git diff --check`: `PASS`.

No plan or apply was performed. Before either operation, verify temporary
`sumak-dev` credentials with STS and match account `632080579751`; deployment
also requires explicit authorization, the SCRUM-46 control plane, reviewed
inputs, current account inventory, and a teardown plan. Static checks are not
runtime, HA, capacity, security, cost, or production-readiness evidence.

## Authoritative references

- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`.
- `docs/01_Producto/Requisitos_Trazados/RTO_IAC.md` (RTO-IAC-06).
- `docs/01_Producto/Requisitos_Trazados/RTO_HA.md` (RTO-HA-03).
- `docs/01_Producto/Requisitos_Trazados/RTO_SEC.md` (RTO-SEC-01).
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`.
- `docs/06_AWS/02_Servicios_y_PoC.md` (P01, P02, P03, P05, and P14).
- `docs/06_AWS/04_PoC_y_registro_de_decisiones_bloqueantes.md` (AWS-02).
- `infra/evidence/SCRUM-30-learner-lab-validation.md`.
- `infra/evidence/SCRUM-39-dev-teardown-recovery-runbook.md`.
