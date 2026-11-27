# SCRUM-31 — Private SSM bastion evidence

## Bounded scope

- Environment: DEV only
- Region: `us-east-1`
- Access path: AWS Systems Manager Session Manager
- Network: private application subnet, no public IP, no inbound rules, no SSH
- IAM: existing Learner Lab `LabInstanceProfile`; no custom IAM resources

The stack includes private `ssm`, `ssmmessages`, and `ec2messages` interface
endpoints. It excludes databases, permanent credentials, public
administration, custom IAM, cross-account access, QA, and PROD.

## Validation evidence

| Check | Status | Evidence |
|---|---|---|
| Terraform formatting | PASS | `terraform fmt -check -recursive` exited 0. |
| Terraform validation | PASS | Terraform 1.17.2; module and DEV root initialized with `-backend=false` and validated. Initial provider deprecation was corrected (`aws_region.region`); validation then exited 0 without warnings. |
| Static security policy tests | PASS | `python3 -m unittest discover -s tests -v`: 31 tests passed. |
| Authorized apply | PASS | Apply completed: 8 add, 0 change, 0 destroy. |
| Instance runtime configuration | PASS | Instance is running; both EC2 health checks are OK; no public IP; private application subnet; `t3.small`; encrypted 20-GiB gp3 root; IMDSv2 required; existing `LabInstanceProfile`/`LabRole` with `AmazonSSMManagedInstanceCore`. |
| Bastion security group | PASS | Zero ingress; only TCP/443 egress by security-group reference to the endpoint security group. |
| SSM endpoints | PASS | All three endpoints (`ssm`, `ssmmessages`, `ec2messages`) are available with private DNS enabled. |
| SSM managed node | PASS | Online; Amazon Linux SSM agent version `3.3.5828.0`. |
| Session lifecycle API | PASS | `StartSession` API created an active Connected session; `terminate-session` ended it. Local interactive console was not exercised because SessionManagerPlugin is absent. |
| Unauthorized/revoked identity denial | NOT_RUN | Denial and revocation behavior remains unverified. |
| Live regional service quota query | BLOCKED_AWS_PERMISSION | `servicequotas:GetServiceQuota` remains denied by Learner Lab identity. The pre-apply observation was 0 running EC2/0 vCPU; post-apply observed total is 1 `t3.small`/2 vCPU against documented project boundaries. This is not live quota proof. |
| Post-apply Terraform plan | PASS | Reported no changes. |

`NOT_RUN` is not `PASS`. The API session lifecycle result does not establish
local interactive-console operation or unauthorized/revoked identity denial.
The live service-quota lookup remains blocked; observed usage and documented
project boundaries do not prove the live AWS quota. No identifiers, account
IDs, IPs, credentials, Terraform state, or plan files are included as evidence.

## Authoritative references

- `docs/01_Producto/Requisitos_Trazados/RTO_NET.md` (`RTO-NET-04`)
- `docs/01_Producto/Requisitos_Trazados/RTO_SEC.md`
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`
- `docs/06_AWS/02_Servicios_y_PoC.md`
- `docs/06_AWS/03_Mapa_de_recursos_y_dependencias_por_cuenta.md`
- `docs/06_AWS/04_PoC_y_registro_de_decisiones_bloqueantes.md`
- `docs/13_Pruebas/01_Plan_de_pruebas_y_calidad.md`
