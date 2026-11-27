# SCRUM-32 Network Security Boundary Evidence

**Status:** IMPLEMENTED_PLAN_ONLY

## Bounded result

The reusable `infra/modules/network-security-groups` module defines explicit
least-privilege security groups for the ALB, logical gateway, mobile and admin
BFFs, application services, service-owned databases, approved brokers, the
private SSM bastion, and private management endpoints.

All internal flows use security-group references. Listener ports, service
ownership, broker access, management endpoints, VPC ID, and reviewed ALB
origins are caller inputs. No undocumented numeric port is embedded.

## Requirement traceability

| Requirement | Implemented evidence |
|---|---|
| `RTO-NET-01` | Only the ALB has CIDR ingress; application and data groups have private SG-reference rules. |
| `RTO-NET-02` | ALB-to-gateway flow is explicit and parameterized; ALB provisioning, TLS, WAF, health checks, and multi-AZ behavior remain outside this module. |
| `RTO-NET-03` | Logical gateway, mobile BFF, and admin BFF boundaries are separate. |
| `RTO-NET-04` | The SSM bastion has no ingress rules and can reach only declared management endpoint groups. |
| `RTO-NET-05` | East-west access uses explicit SG references; no peering or general environment connectivity is created. |
| `RTO-NET-06` | The reviewed ALB listener can carry TLS/WSS; WebSocket provisioning and runtime authorization remain outside scope. |
| `RNF-SEC-15` | BFF-to-service, service-to-owned-database, and service-to-broker permissions are explicit allowlists. |
| `RTO-IAC-01` | The boundary is represented as reusable Terraform. |
| `RTO-IAC-06` | Static tests inspect public ingress, internal SG references, ownership boundaries, and parameterized ports. |
| `RTO-DATA-02` | A database group accepts traffic only from its owning service; no consumer-to-foreign-database path exists. |

## Explicit exclusions

- No `terraform apply` and no AWS resources created.
- No VPC, subnet, route, peering, TGW, VPN, Direct Connect, IAM role, IRSA, or
  cross-account access.
- No public SSH or public data/internal endpoint.
- No claim that ALB, WAF, TLS, SSM, database, broker, capacity, availability,
  backup, RPO/RTO, or compliance controls work at runtime.
- No update to the ignored `docs/` source of truth.

## Validation evidence

| Check | Result | Evidence |
|---|---|---|
| Terraform formatting | PASS | `terraform fmt -check -recursive infra/modules/network-security-groups` returned no differences. |
| Terraform validation | PASS | Terraform reported `Success! The configuration is valid.` |
| Static security tests | PASS | `python3 -m unittest discover -s tests -v` ran 15 tests, including 6 SG-boundary tests, with `OK`. |
| Direct AWS-backed plan | BLOCKED_PERMISSIONS | No valid AWS credential source was available. This result is not PASS and no credential control was bypassed. |
| Offline structural plan | PASS | A temporary provider configuration that disables AWS API calls produced `Plan: 34 to add, 0 to change, 0 to destroy`; the saved plan is outside Git at `/tmp/opencode/scrum-32.tfplan`. |
| Terraform apply | NOT_RUN | Explicitly excluded by SCRUM-32. |
| AWS runtime probes | NOT_RUN | VPC, TLS/WAF, SSM, data, broker, and connectivity behavior require separately authorized infrastructure. |

The offline plan uses documentation-only example addresses and fixture ports to
exercise the module graph. It is static review evidence, not an account plan,
runtime evidence, authorization to apply, or proof that the referenced VPC and
services exist.

The saved plan remains outside Git and must not be applied. No state or plan
file is part of this change.
