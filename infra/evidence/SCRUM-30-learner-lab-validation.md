# SCRUM-30 Learner Lab Validation Evidence

**Status:** PASS

**Validation window:** 2026-11-24 01:19-01:56 UTC

**Account:** `****9751` (redacted)

**Project regions:** `us-east-1`, `us-west-2`

## Scope and PASS meaning

This PASS confirms the bounded SCRUM-30 objective: validate Learner Lab
constraints, pre-provisioned roles, selected service quotas, controlled
`iam:PassRole`, PostgreSQL RDS class availability, and cleanup of residual EC2
instances.

It does not mean that the DEV architecture is provisioned or that runtime EKS,
RDS, ALB, availability, capacity, RPO/RTO, compliance, or production readiness
has passed. No validation resource was created.

## Binding guardrails

| Area | Binding project constraint |
|---|---|
| Regions | `us-east-1` primary and `us-west-2` DR; use physical AZ IDs. |
| EC2 count | Maximum 9 running instances per account across regions and services, including EKS nodes and indirectly launched instances. |
| EC2 capacity | Maximum 32 running EC2 vCPU per region; On-Demand only; sizes from `nano` through `large`. |
| EBS | Maximum 100 GB per volume; `gp2`, `gp3`, `sc1`, or `standard`; no PIOPS. |
| RDS | Class no larger than `medium`; maximum 100 GB `gp2`; On-Demand; no Enhanced Monitoring. |
| IAM | Use pre-provisioned roles and profiles; do not create IAM users, groups, or roles; do not assume IRSA or cross-account access. |
| ECR | Treat `LabRole` as read-only under the documented baseline; use the authorized lab principal for writes; no cross-account replication; consume immutable digests. |

Larger values exposed by AWS Service Quotas do not supersede these Learner Lab
and SUMAK limits.

## Live identity and pre-provisioned roles

The live caller was a temporary `voclabs` assumed-role session in account
`****9751`. The following pre-provisioned identities were visible:

- `LabRole`.
- `LabInstanceProfile`, associated with `LabRole`.
- A generated `...-LabEksClusterRole-...` role.
- A generated `...-LabEksNodeRole-...` role.
- `RoleForLambdaModLabRole`.

`LabRole` exposes the expected SSM, EKS, ECR read-only, EKS worker-node, and
VocLab custom managed policy attachments. The generated EKS cluster and node
roles expose the expected EKS and EC2 trust relationships and managed policies.

## EC2 cleanup evidence

### Before cleanup

| Region | Non-terminated instances | Composition |
|---|---:|---|
| `us-east-1` | 6 | Four `t2.nano` and two `t3.micro` classroom residual instances. |
| `us-west-2` | 0 | None. |

The six exact instances in `us-east-1` were passed to the explicitly authorized
`terminate-instances` operation. AWS accepted all six and changed them from
`running` to `shutting-down`.

### Final state

- A subsequent exact-ID lookup reported all six instances as `terminated`.
- A final count filtered to `pending`, `running`, `stopping`, and `stopped`
  returned `0` in `us-east-1`.
- The same final count returned `0` in `us-west-2`.
- Observed use in the two permitted project regions is therefore **0/9**.

Inventory outside the two project regions is not claimed as exhaustive because
sampled calls were denied or unavailable there. No EC2 instance was created by
this validation.

## Controlled `iam:PassRole` validation

The caller's effective policy was evaluated with:

- The exact pre-provisioned `LabRole` as the resource.
- Complete `iam:PassedToService`, requested-region, and token-issue-time
  context.
- `us-east-1` as the requested project region.

| Passed-to service | Decision | Missing context |
|---|---|---|
| `eks.amazonaws.com` | `allowed` | None |
| `ec2.amazonaws.com` | `allowed` | None |
| `rds.amazonaws.com` | `allowed` | None |

This is a live IAM policy simulation result. It validates the evaluated
`iam:PassRole` policy path but is not a runtime EKS, EC2, or RDS creation test.
No role was changed or newly assumed.

## PostgreSQL RDS availability

Read-only `describe-orderable-db-instance-options` calls confirmed PostgreSQL
offerings for both requested classes in both project regions:

| Region | Class | Options observed | Sample properties |
|---|---|---:|---|
| `us-east-1` | `db.t3.micro` | At least 200; response was paginated | PostgreSQL, VPC-capable, `gp2`. |
| `us-east-1` | `db.t4g.micro` | 180 | PostgreSQL, VPC-capable, `gp2`. |
| `us-west-2` | `db.t3.micro` | 180 | PostgreSQL, VPC-capable, `gp2`. |
| `us-west-2` | `db.t4g.micro` | 148 | PostgreSQL, VPC-capable, `gp2`. |

The counts represent returned orderable engine/version/storage combinations,
not instance capacity guarantees. The paginated `us-east-1` `db.t3.micro`
result is recorded as a minimum rather than a total.

The caller's `rds:CreateDBInstance` policy was also simulated with complete
contexts for:

- PostgreSQL.
- `db.t3.micro` and `db.t4g.micro`.
- 20 GB `gp2` storage and 0 PIOPS.
- On-Demand/default-tenancy context.
- `us-east-1` and `us-west-2`.

All four region/class combinations evaluated as `allowed` with no missing
context. This is policy evidence, not a runtime create. Final inventory calls
returned zero RDS DB instances in both project regions, so no RDS cleanup was
required.

## Service quota observations

`ListServiceQuotas` exposed these account/service values in the project regions:

| Service | Exposed quota | Interpretation |
|---|---:|---|
| EKS clusters | 100 per region | Account quota only; not a SUMAK capacity target. |
| EKS managed node groups | 30 per cluster | Still bounded by 9 EC2 per account and 32 vCPU per region. |
| EKS nodes | 450 per managed node group | Not usable as a Learner Lab capacity claim. |
| VPC | 5 per region | Does not by itself authorize provisioning. |
| NAT gateway | 5 per AZ | Does not guarantee lab permission or budget. |
| ALB | 50 per region | Does not validate runtime ingress behavior. |
| RDS DB instances | 40 per region | RDS class and storage guardrails still control. |
| ECR `PutImage` | Rate 10; service unit `None` | API-rate quota, not repository capacity or push proof. |
| EC2 Standard On-Demand vCPU | 256 observed in `us-west-2` | The binding Learner Lab limit remains 32 vCPU per region. |

Direct `GetServiceQuota` remained denied for selected EC2, EKS, VPC, ALB, RDS,
and ECR quotas. The successful list values are therefore retained as
observations, not as permission or capacity guarantees.

## Acceptance results

| Acceptance item | Result | Evidence |
|---|---|---|
| Residual EC2 cleanup | PASS | All six exact instances reached `terminated`. |
| EC2 use in project regions | PASS | Zero non-terminated instances in each region; observed use 0/9. |
| Pre-provisioned roles | PASS | `LabRole`, `LabInstanceProfile`, and generated EKS roles are visible. |
| Controlled `iam:PassRole` | PASS | `allowed`, no missing context, for EKS, EC2, and RDS service contexts. |
| PostgreSQL class availability | PASS | Both requested classes are orderable in both project regions. |
| Controlled RDS create-policy evaluation | PASS | All four region/class combinations are `allowed` with no missing context. |
| Validation resource cleanup | PASS | No validation resource was created; no RDS/EKS/ALB/ECR cleanup is pending. |

## Remaining limitations outside the PASS boundary

- The complete authoritative F07 source is absent from the local tree; local
  governance records its hash and Confluence reference.
- Custom VocLab policy documents and selected role details remain hidden by
  explicit identity-policy denies.
- Direct `GetServiceQuota` is denied.
- Non-project regions were not exhaustively inventoried.
- No account-to-environment evidence distinguishes `sumak-dev` from
  `sumak-dev-integration`.
- The target DEV VPC, EKS, ALB, private RDS, ECR, SSM, and analytics resources
  are not provisioned. Provisioning is outside SCRUM-30.
- Actual EKS and RDS creation still requires a separately authorized bounded
  PoC, reviewed Terraform plan, and cleanup plan.

## Sanitized command evidence

The live validation used sanitized forms of these commands:

```bash
aws sts get-caller-identity
aws iam list-roles
aws iam list-instance-profiles
aws iam get-role --role-name LabRole
aws iam list-attached-role-policies --role-name LabRole
aws iam simulate-principal-policy \
  --policy-source-arn '<REDACTED_CALLER_ROLE_ARN>' \
  --action-names iam:PassRole \
  --resource-arns '<REDACTED_LABROLE_ARN>' \
  --context-entries '<COMPLETE_CONTEXT>'

aws ec2 describe-instances --region '<PROJECT_REGION>'
aws ec2 terminate-instances --region us-east-1 \
  --instance-ids '<SIX_AUTHORIZED_INSTANCE_IDS>'
aws ec2 describe-instances --region us-east-1 \
  --instance-ids '<SIX_AUTHORIZED_INSTANCE_IDS>'

aws rds describe-orderable-db-instance-options \
  --engine postgres \
  --db-instance-class '<DB_CLASS>' \
  --region '<PROJECT_REGION>'
aws iam simulate-principal-policy \
  --policy-source-arn '<REDACTED_CALLER_ROLE_ARN>' \
  --action-names rds:CreateDBInstance \
  --context-entries '<POSTGRES_CLASS_STORAGE_REGION_CONTEXT>'
```

No request ID, authorization ID, pagination token, full ARN, account number,
temporary credential, or raw large response is retained in this evidence.

## Local sources

- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`, lines 28-34.
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`, lines 14-28 and 70.
- `docs/06_AWS/02_Servicios_y_PoC.md`, EKS, RDS, ECR, and PoC sections.
- `docs/06_AWS/03_Mapa_de_recursos_y_dependencias_por_cuenta.md`, DEV account
  resource maps.
- `docs/06_AWS/04_PoC_y_registro_de_decisiones_bloqueantes.md`, evidence and PoC
  requirements.
- `docs/15_Requerimientos_v2_5_ORIGINAL/Requerimientos_v2_5_ORIGINAL_RECIEN_ENTREGADO.md`,
  RTO-AWS and RTO-SEC constraints cited by the delegated documentation review.

The local source files remained read-only and were not modified.
