# SCRUM-36 — DEV application load balancer evidence

- Scope: reusable ALB module and DEV-only Terraform root.
- Implementation status: `IMPLEMENTED_PLAN_ONLY`.
- Infrastructure plan/apply: `NOT_RUN`.
- Runtime TLS, WSS, target health, connection draining, and origin protection: `NOT_RUN`.
- External dependency: `BLOCKED_EXTERNAL_DEPENDENCY` because SCRUM-35 found no
  authorized domain, hosted zone, or ACM certificate.

## Implemented behavior

- Public application load balancer across the existing DEV public subnets.
- Existing ALB security group consumed from the `network-boundaries` state.
- Private IP target group for the logical gateway using HTTP/2, parameterized
  health checks, connection draining, and idle timeout.
- HTTPS listener modeled but disabled until an authorized ACM certificate ARN
  is available.
- DNS, WAF, IAM, VPC, subnet, inter-account, QA, and PROD resources excluded.

## Validation evidence

- `terraform fmt -recursive infra`: PASS.
- `terraform init -backend=false && terraform validate` in the DEV ALB root:
  PASS with Terraform provider `hashicorp/aws` 6.74.0.
- `terraform init -backend=false && terraform validate` in the DEV
  `network-boundaries` root: PASS.
- `python3 -m unittest tests.test_dev_alb_boundaries -v`: PASS (4 tests).
- `python3 -m unittest discover -s tests -v`: PASS (41 tests).
- `git diff --check`: PASS.

No plan or apply was performed because deployment was not authorized and the
TLS prerequisite is unresolved. These static results are not runtime, HA,
capacity, security, or production-readiness evidence.

## Operational access constraint

If any AWS account other than the currently active DEV account is required,
ask the user to activate access first; normally only AWS DEV access is enabled.

## Authoritative references

- `docs/01_Producto/Requisitos_Trazados/RTO_NET.md` (RTO-NET-02).
- `docs/01_Producto/Requisitos_Trazados/RTO_IAC.md` (RTO-IAC-06).
- `docs/06_AWS/02_Servicios_y_PoC.md` (P02).
- `docs/06_AWS/04_PoC_y_registro_de_decisiones_bloqueantes.md` (AWS-04).
- `infra/evidence/SCRUM-35-acm-dns-tls-poc.md`.
