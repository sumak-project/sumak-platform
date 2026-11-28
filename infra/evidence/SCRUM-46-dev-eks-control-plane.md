# SCRUM-46 — DEV EKS control-plane evidence

## Scope and implementation

- Scope: Terraform module and `sumak-dev` root composition for one DEV EKS
  control plane plus the existing bounded managed node group.
- Control plane: uses a generated Learner Lab role whose name contains
  `LabEksClusterRole`, three supplied private subnets, private-only API endpoint
  access, and configured EKS control-plane logs. No role has the literal name
  `LabEksClusterRole`.
- Private connectivity: EC2, ECR API, and ECR DKR interface endpoints with
  private DNS plus an S3 gateway endpoint on the three DEV private route tables.
  Interface endpoint ingress is limited to TCP/443 from the DEV VPC CIDR.
- Node group: consumes that cluster and uses a generated Learner Lab role whose
  name contains `LabEksNodeRole`, three
  On-Demand `t3.large` nodes, and encrypted `gp2` root volumes bounded to
  100 GiB. The module does not create IAM roles, VPCs, or subnets.
- Backend: same-account S3 state with native `use_lockfile = true`; remote
  backend initialization and native lock usage succeeded for this review.
- Sequencing: proceeding despite the SCRUM-40 sequencing ambiguity was
  explicitly authorized by the user. This records sequencing authorization,
  not approval to apply infrastructure or evidence that any pending PoC passed.

## Configuration and operational constraints

- Root: `infra/accounts/sumak-dev/us-east-1/dev/eks/`; module:
  `infra/modules/eks-control-plane/`.
- Inputs include the generated Learner Lab role ARNs, three private subnet IDs,
  three corresponding distinct availability zones, and Kubernetes minor
  version `1.36` (default). Live EKS supported versions were `1.32`–`1.37`.
- Live inventory: STS account `632080579751` (`PASS`); three private application
  subnets in the same VPC across `us-east-1a/b/c`, public-IP mapping disabled
  (`PASS`); one existing running `t3.small`; EKS cluster inventory empty; state
  backend bucket accessible.
- Generated roles containing `LabEksClusterRole` and `LabEksNodeRole` existed
  with expected EKS/EC2 trust and managed policies. IAM policy simulation
  returned `iam:PassRole` allowed. Role input validation was updated to accept
  these generated names in the assigned account.
- Earlier reads were denied by `voc-cancel-cred`; renewed AWS access resolved
  that blocker for the inventory and plan evidence in this record.
- Learner Lab bounds: at most 9 running EC2 instances/account, 32 running EC2
  vCPUs/region, instance type no larger than `large`, and EBS no larger than
  100 GB using an allowed type. Inventory must include EKS-launched capacity.
- No QA/PROD, custom IAM, IRSA, `AssumeRole`, application/service deployment,
  SCRUM-47 database roles, real PII or votes, or unsupported readiness,
  availability, security, or capacity claims.
- Any Terraform apply requires separate explicit approval after a fresh
  reviewed plan, verified inventory/roles/quota headroom, and approved teardown
  and recovery preparation.

## Validation evidence

Executed locally for this change:

| Check | Result |
|---|---|
| `terraform fmt -check -recursive infra` | `PASS` |
| EKS root backend-free `terraform init` | `PASS`; `hashicorp/aws` 6.74.0 |
| EKS root `terraform validate` | `PASS` |
| Focused EKS control-plane, node-group, and private-connectivity boundary tests | `PASS` |
| `python3 -m unittest discover -s tests -v` | `PASS` (71 tests) |
| `git diff --check` | `PASS` |
| Remote backend init and native S3 lock usage | `PASS` |
| Corrective remote Terraform plan | `PASS`; five connectivity creates and replacement of only the failed node group |
| Corrective Terraform apply | `PASS`; 6 added, 0 changed, 1 destroyed |
| EKS managed node group | `PASS`; `ACTIVE`, no health issues, desired/min/max 3 |
| EC2 node inventory | `PASS`; three running private `t3.large`, one per supplied subnet, no public IPs |
| Direct Kubernetes API / health Pod | `NOT_RUN`; the private SSM bastion cannot reach the cluster security group, and access was not broadened |

AWS evidence and limits:

- The initial apply created the control plane and launch template, but the node
  group ended in `CREATE_FAILED` / `NodeCreationFailure` because private nodes
  could not reach the EC2 API.
- The corrective apply added the required private AWS API connectivity and
  replaced only that failed node group. Saved plans remained under
  `/tmp/opencode` and are not committed.
- Direct Kubernetes API node/Pod verification and a health-Pod test remain
  `NOT_RUN`. A bounded SSM-bastion attempt timed out at the private API endpoint;
  the ticket did not broaden cluster security-group access. The managed node
  group `ACTIVE` status proves successful EKS registration but is not direct Pod
  health evidence. Teardown remains `NOT_RUN`.

## Teardown and recovery

Follow `infra/evidence/SCRUM-39-dev-teardown-recovery-runbook.md`. It requires
explicit change approval, verified account/region/resource ownership, a
reconciled live inventory and Terraform state, protected recovery material,
and a reviewed plan. It does not itself authorize teardown. Do not remove or
force-delete state locks to bypass an active writer.

## Authoritative references

- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_IAC.md`,
  `RTO_NET.md`, and `RNF_SEC.md`
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`,
  `02_Servicios_y_PoC.md`, `03_Mapa_de_recursos_y_dependencias_por_cuenta.md`,
  and `04_PoC_y_registro_de_decisiones_bloqueantes.md`
- `infra/evidence/SCRUM-30-learner-lab-validation.md` (prior evidence, not
  current inventory or authorization)
- `infra/evidence/SCRUM-37-terraform-state-backend.md`
- `infra/evidence/SCRUM-39-dev-teardown-recovery-runbook.md`
- `infra/evidence/SCRUM-40-dev-eks-managed-node-group.md`
- `infra/accounts/sumak-dev/us-east-1/dev/eks/README.md`

Ignored `docs/` remains read-only and was not modified.
