# DEV EKS Terraform root

This Terraform root declares the `sumak-dev` EKS control plane and its bounded
managed node group. It is configuration only: a successful local validation
does not mean that AWS resources were planned, applied, or checked at runtime.

## Scope and inputs

The root is pinned to AWS account `632080579751`, region `us-east-1`, and the
`sumak-dev` profile. Supply reviewed values through a protected local
`*.tfvars` file or equivalent approved input mechanism; never commit credentials,
state, plans, or sensitive values.

| Input | Meaning / constraint |
|---|---|
| `cluster_role_arn` | ARN of an existing generated Learner Lab role containing `LabEksClusterRole` in its name, in account `632080579751`. |
| `node_role_arn` | ARN of an existing generated Learner Lab role containing `LabEksNodeRole` in its name, in account `632080579751`. |
| `cluster_version` | Kubernetes minor version; defaults to `1.36`, constrained to the live-supported `1.32`–`1.37` set recorded for this review. |
| `private_subnet_ids` | Exactly three distinct existing private subnet IDs. |
| `availability_zones` | Exactly three distinct zones corresponding to those subnets. |
| `root_volume_size` | Node root EBS size in GiB; defaults to 50 and is bounded to 20–100. |

The control plane uses private endpoint access only, enables the five configured
EKS control-plane log types, and consumes the three supplied subnet IDs. Private
node bootstrap and image access use interface endpoints for EC2, ECR API, and
ECR DKR plus an S3 gateway endpoint on the three private route tables. The
interface endpoint security group accepts only TCP/443 from the VPC CIDR. The
managed node group uses exactly three On-Demand `t3.large` instances, fixed
min/desired/max size 3, and encrypted `gp2` root volumes. It creates neither
IAM roles nor VPC/subnets, service workloads, or resources in another
environment.

## Learner Lab limits and operational boundary

Treat these as hard limits, not targets: at most 9 running EC2 instances per
account, at most 32 running EC2 vCPUs per region, instance size no larger than
`large`, and EBS volumes no larger than 100 GB with an allowed volume type.
Live checks for this review confirmed STS account `632080579751`; three
same-VPC private application subnets in `us-east-1a`, `us-east-1b`, and
`us-east-1c`, each with public-IP mapping disabled; one existing running
`t3.small`; and no existing EKS clusters. The state backend bucket was
accessible. Live IAM inventory found no role literally named
`LabEksClusterRole`; generated Learner Lab roles containing `LabEksClusterRole`
and `LabEksNodeRole` were present with the expected EKS/EC2 trust and managed
policies. Policy simulation reported `iam:PassRole` allowed. The root input
validation accepts those generated role-name patterns, restricted to the
assigned account.

Earlier reads during this ticket were denied by `voc-cancel-cred`; that blocker
was resolved for the renewed-access validation above. Inventory and authorization
claims here describe that review window only. Do not create custom IAM, use
IRSA/AssumeRole, or treat policy simulation as proof of successful resource
creation.

## Backend and validation workflow

The root uses the same-account encrypted S3 backend in `us-east-1` with
`use_lockfile = true`. Backend-free initialization does not exercise remote
state access or lock permissions. See
[`../state-backend/README.md`](../state-backend/README.md) for backend safety,
recovery, and lock handling.

Run local configuration checks from the repository root:

```bash
terraform fmt -check -recursive infra
terraform -chdir=infra/accounts/sumak-dev/us-east-1/dev/eks init -backend=false -lockfile=readonly
terraform -chdir=infra/accounts/sumak-dev/us-east-1/dev/eks validate
python3 -m unittest tests.test_dev_eks_control_plane_boundaries tests.test_dev_eks_managed_node_group_boundaries tests.test_dev_private_aws_api_connectivity_boundaries -v
python3 -m unittest discover -s tests -v
git diff --check
```

Local checks validate formatting, Terraform syntax/provider schemas, and static
repository boundaries; they do not establish runtime behavior.

Remote backend initialization and native S3 lock usage succeeded. The initial
apply created the control plane and launch template, but the node group failed
because private nodes could not reach the EC2 API. An approved corrective plan
created the three interface endpoints, S3 gateway endpoint, and endpoint
security group, then replaced only the failed node group. The apply completed
with **6 additions, 0 changes, and 1 destruction**. Saved plans remained only
under `/tmp/opencode`; never commit plans, state, credentials, or sensitive
inputs. Never apply to QA or PROD.

## Runtime, teardown, and evidence

The corrective apply completed successfully. AWS reports the node group
`ACTIVE`, with no health issues and three private `t3.large` instances without
public IP addresses, distributed across the three supplied subnets. Direct
Kubernetes API and health-Pod checks remain `NOT_RUN`: the existing SSM bastion
cannot reach the cluster security group, and no access rule was broadened for
this ticket. Teardown also remains `NOT_RUN`; this deployment evidence does not
establish production readiness, capacity, availability, or broad runtime
security.

Use [`../../../../../evidence/SCRUM-39-dev-teardown-recovery-runbook.md`](../../../../../evidence/SCRUM-39-dev-teardown-recovery-runbook.md)
for the approval-bound, inventory-first teardown and recovery procedure. That
runbook is guidance, not authorization to destroy resources.

## Authoritative references

- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_IAC.md`,
  `RTO_NET.md`, and `RNF_SEC.md`
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`,
  `02_Servicios_y_PoC.md`, `03_Mapa_de_recursos_y_dependencias_por_cuenta.md`,
  and `04_PoC_y_registro_de_decisiones_bloqueantes.md`
- `infra/evidence/SCRUM-30-learner-lab-validation.md` — prior evidence and its
  stated limitations; not current authorization or inventory
- `infra/evidence/SCRUM-37-terraform-state-backend.md` and
  `../state-backend/README.md` — backend and locking boundaries
- `infra/evidence/SCRUM-39-dev-teardown-recovery-runbook.md`
- `infra/evidence/SCRUM-40-dev-eks-managed-node-group.md` — node-group contract
  and external prerequisite evidence
