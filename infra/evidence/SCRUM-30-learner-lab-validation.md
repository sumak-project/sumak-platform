# SCRUM-30 Learner Lab Validation Evidence

**Status:** BLOCKED / PARTIAL (not PASS)

**Validation window:** 2026-11-24 01:19-01:23 UTC

**Account:** `****9751` (redacted)

**Regions checked:** `us-east-1`, `us-west-2`

## Scope and evidence classification

This evidence compares documented SUMAK Learner Lab constraints with read-only
observations from the active AWS account. No resource was created, modified,
deleted, pushed, or assumed. IAM simulation results are policy evaluations, not
runtime proof that a resource can be created.

The full authoritative F07 Learner Lab v1.2 source is not present in the local
tree. Local governance records its hash and points to Confluence page `6324241`;
therefore, derivative local constraints are used here and the missing source is
recorded as a blocker.

Evidence marked proposed, pending, `NOT_RUN`, blocked, or inconclusive is not a
PASS. This validation makes no capacity, availability, RPO/RTO, compliance, or
production-readiness claim.

## Documented guardrails

| Area | Binding project constraint |
|---|---|
| Regions | `us-east-1` primary and `us-west-2` DR; use physical AZ IDs. |
| EC2 count | Maximum 9 running instances per account across all regions and services, including EKS nodes and indirectly launched instances. |
| EC2 capacity | Maximum 32 running EC2 vCPU per region; On-Demand only; sizes from `nano` through `large`. |
| EBS | Maximum 100 GB per volume; `gp2`, `gp3`, `sc1`, or `standard`; no PIOPS. |
| RDS | Class no larger than `medium`; maximum 100 GB `gp2`; On-Demand; no Enhanced Monitoring. |
| IAM | Use only pre-provisioned roles and profiles. Do not create IAM users, groups, or roles; do not assume IRSA or cross-account access. Verify `iam:PassRole`. |
| ECR | Documented baseline treats `LabRole` as read-only and the current lab/console principal as the writer; no cross-account replication; consume immutable digests. |
| DEV topology | Isolated VPC, three planned AZs, public ingress subnets, private application/EKS subnets, private data subnets, ALB/TLS, private RDS, per-account ECR, and conditional SSM/analytics services. |

The 9-instance account limit and 32-vCPU regional limit remain binding even
when AWS Service Quotas exposes larger values.

## Observed account state

### `us-east-1`

- Six running EC2 instances: four `t2.nano` and two `t3.micro`, approximately
  six vCPU total. None has an instance profile.
- The six instances consume 6/9 of the project account guardrail, leaving room
  for at most three additional running instances, subject to ownership and
  cross-region reconciliation.
- Two VPCs exist: a default `172.31.0.0/16` VPC and a non-default
  `10.0.0.0/16` VPC.
- The non-default VPC has four subnets with public-IP-on-launch disabled, but
  they occupy only physical AZ IDs `use1-az2` and `use1-az4`. This is not the
  required three-AZ, three-tier DEV topology.
- No NAT gateway, EKS cluster, ALB/NLB, RDS DB instance, or ECR repository was
  observed.

### `us-west-2`

- No EC2 instance or EKS cluster was observed.
- One default VPC with four public subnets exists.
- No NAT gateway, ALB/NLB, RDS DB instance, or ECR repository was observed.

Inventory calls outside the two project regions were denied in sampled standard
regions or failed credential validation in sampled opt-in regions. The observed
6/9 count is therefore not an exhaustive account-wide inventory and must not be
treated as one.

## IAM and permission findings

The caller is a temporary `voclabs` assumed-role session. The following
pre-provisioned identities were visible:

- `LabRole`.
- `LabInstanceProfile`, associated with `LabRole`.
- A generated `...-LabEksClusterRole-...` role.
- A generated `...-LabEksNodeRole-...` role.
- `RoleForLambdaModLabRole`.

`LabRole` has these visible managed policy attachments:

- `AmazonSSMManagedInstanceCore`.
- `AmazonEKSClusterPolicy`.
- `AmazonEC2ContainerRegistryReadOnly`.
- `AmazonEKSWorkerNodePolicy`.
- Three VocLab custom managed policies whose documents could not be read.

No inline `LabRole` policy was listed. The EKS cluster role trusts
`eks.amazonaws.com` and has the EKS cluster, networking, compute, block storage,
and load-balancing managed policies. The EKS node role trusts
`ec2.amazonaws.com` and has the EKS CNI, ECR read-only, and EKS worker-node
managed policies.

Explicit identity-policy denies blocked inspection of `voclabs`,
`RoleForLambdaModLabRole`, and the custom managed policy documents. This limits
independent verification of the effective policy conditions.

Live IAM policy simulation produced the following results for `voclabs` and
`LabRole`:

| Action group | Simulation result | Interpretation |
|---|---|---|
| EKS cluster/node group creation, EC2 run, ELB creation, ECR repository creation and `PutImage` | `allowed` | Inconclusive for deployment; no runtime create or push occurred. |
| `iam:PassRole` and RDS DB instance creation | `implicitDeny` with missing context keys | Inconclusive; the simulation lacked required regional, service, instance, storage, and role-passing context. |

The ECR simulation does not override the documented `LabRole` read-only
baseline because hidden custom policy conditions were not inspectable and no
push test was authorized.

## Quota observations

`ListServiceQuotas` exposed the following values in both project regions unless
otherwise stated:

| Service | Exposed quota | Project interpretation |
|---|---:|---|
| EKS clusters | 100 per region | AWS account quota only; not proof that EKS creation or `PassRole` works. |
| EKS managed node groups | 30 per cluster | Still bounded by 9 EC2 per account and 32 vCPU per region. |
| EKS nodes | 450 per managed node group | Not usable as a SUMAK capacity target. |
| VPC | 5 per region | Does not authorize creation. |
| NAT gateway | 5 per AZ | Does not authorize creation or guarantee budget. |
| ALB | 50 per region | Does not validate TLS, WSS, gRPC, or runtime creation. |
| RDS DB instances | 40 per region | RDS class/storage restrictions and permission PoC still control. |
| ECR `PutImage` | Rate 10; service unit reported as `None` | API-rate quota, not repository capacity or push authorization. |
| EC2 Standard On-Demand vCPU | 256 in `us-west-2`; target value not returned in the first paginated `us-east-1` result | The documented 32-vCPU Learner Lab limit controls. |

Direct `GetServiceQuota` was denied for every selected EC2, EKS, VPC, ALB, RDS,
and ECR quota in both regions. Consequently, the list values cannot be treated
as a complete statement of applied Learner Lab restrictions.

## Required DEV resources versus observation

| Required candidate capability | Observation | Status |
|---|---|---|
| Three-AZ isolated DEV VPC with public ingress, private app/EKS, and private data tiers | Existing non-default VPC spans two physical AZ IDs and does not expose the required tiers in this validation. | BLOCKED |
| EKS cluster and bounded managed node group | No cluster exists; `PassRole` remains inconclusive; only three instance slots remain before reconciliation. | BLOCKED |
| ALB/TLS ingress | No load balancer exists; creation was not tested. | NOT_RUN |
| Private PostgreSQL RDS within Learner Lab sizing | No DB instance exists; effective creation permission remains inconclusive. | BLOCKED |
| Per-account ECR with approved immutable digest flow | No repository exists; no push/pull test was authorized. | NOT_RUN |
| SSM private bastion | `LabInstanceProfile` and SSM policy are visible, but no instance is associated and no SSM session was tested. | NOT_RUN |

## Blockers and restrictions

1. The complete authoritative F07 source is missing locally.
2. No evidence maps account `****9751` to `sumak-dev` or
   `sumak-dev-integration`.
3. Effective `iam:PassRole` and RDS creation permissions remain inconclusive.
4. Explicit denies prevent reading the custom managed policy documents and
   selected role details.
5. Direct `GetServiceQuota` is denied.
6. No authorized EKS/RDS/ALB creation or ECR push test was performed.
7. Account-wide EC2 inventory outside the two project regions could not be
   completed.
8. Six of the nine permitted running EC2 slots are already consumed in
   `us-east-1`; ownership and purpose are unknown from this validation.
9. The required DEV architecture is not provisioned, so runtime behavior is
   unvalidated.

## Decision and next authorized checks

Do not run `terraform apply` or create an EKS node group until the six existing
EC2 instances are reconciled and an account-wide capacity decision preserves
the 9-instance limit. Terraform policy checks must retain the 9-instance,
32-vCPU, maximum-`large`, EBS, and RDS guardrails regardless of larger service
quota values.

With explicit authorization and a cleanup plan, run bounded PoCs in this order:

1. Evaluate `iam:PassRole` with complete context for the pre-provisioned EKS
   cluster and node roles; then perform the smallest approved EKS creation test.
2. Create the smallest approved PostgreSQL RDS test within `medium`, 100 GB
   `gp2`, private-only constraints; verify required extensions/TLS and clean up.
3. Use the authorized lab/console principal for an ECR push and pull, record the
   immutable digest, and clean up.
4. Re-run account inventory and quota evidence, then update this record without
   converting pending or blocked evidence into PASS prematurely.

## Reproducible read-only command set

The validation used sanitized forms of these command categories:

```bash
aws sts get-caller-identity
aws iam list-roles
aws iam list-instance-profiles
aws iam get-role --role-name LabRole
aws iam list-attached-role-policies --role-name LabRole
aws iam list-role-policies --role-name LabRole
aws iam simulate-principal-policy --policy-source-arn '<REDACTED_ROLE_ARN>' \
  --action-names '<ACTION>...'

aws ec2 describe-regions --all-regions --region us-east-1
aws ec2 describe-instances --region '<REGION>'
aws ec2 describe-vpcs --region '<REGION>'
aws ec2 describe-subnets --region '<REGION>'
aws ec2 describe-nat-gateways --region '<REGION>'
aws eks list-clusters --region '<REGION>'
aws elbv2 describe-load-balancers --region '<REGION>'
aws rds describe-db-instances --region '<REGION>'
aws ecr describe-repositories --region '<REGION>'
aws service-quotas list-service-quotas --service-code '<SERVICE>' \
  --region '<REGION>'
```

No request ID, authorization ID, pagination token, full ARN, temporary
credential, or raw large response is retained in this repository evidence.

## Local sources

- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`, lines 28-34.
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`, lines 14-28 and 70.
- `docs/06_AWS/02_Servicios_y_PoC.md`, sections covering EKS, RDS, ECR, and PoC
  gates.
- `docs/06_AWS/03_Mapa_de_recursos_y_dependencias_por_cuenta.md`, DEV account
  resource maps.
- `docs/06_AWS/04_PoC_y_registro_de_decisiones_bloqueantes.md`, evidence and PoC
  requirements.
- `docs/15_Requerimientos_v2_5_ORIGINAL/Requerimientos_v2_5_ORIGINAL_RECIEN_ENTREGADO.md`,
  RTO-AWS and RTO-SEC constraints cited by the local evidence review.

These local files remain read-only and were not modified.
