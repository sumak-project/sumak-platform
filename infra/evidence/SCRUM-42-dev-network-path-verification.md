# SCRUM-42 — DEV network path verification

**Status:** CONFIGURATION_VERIFIED
**Infrastructure change:** NOT_RUN
**Terraform plan/apply:** NOT_RUN
**AWS runtime verification:** NOT_RUN

## Bounded scope

Verify the tracked DEV Terraform configuration for the documented allowed
network chain and fail closed when prohibited connectivity is introduced. This
ticket does not provision or modify AWS resources.

The allowed path is limited to reviewed ingress through the ALB security group,
then the logical gateway, client BFFs, internal gRPC services, and each service's
owned data store or approved broker. Security-group hops use source security
group references instead of public CIDRs.

The denied paths are:

- public SSH or unrestricted CIDR ingress;
- unrestricted protocols or default Internet security-group egress;
- IGW, NAT, peering, Transit Gateway, or VPN routes from private tiers;
- VPC peering, Transit Gateway, VPN, or cross-environment attachments; and
- public IPv4 assignment for application or data subnets.

Only public-ingress route tables may route `0.0.0.0/0` to the Internet Gateway.
NAT gateways and private AWS endpoints remain deferred pending a concrete,
reviewed requirement, permissions, and cost review.

## Requirement traceability

| Reference | Bounded evidence intent |
|---|---|
| `RTO-NET-01` | Keep public ingress explicit while application and data tiers remain private. |
| `RTO-NET-02` | Verify the configured public-facing path without claiming an active ALB or runtime endpoint. |
| `RTO-NET-03` | Reject unrestricted security-group protocols and Internet egress. |
| `RTO-NET-04` | Reject public SSH ingress; administrative access remains SSM-only. |
| `RTO-NET-05` | Reject general peering, TGW, VPN, and undocumented cross-network routes. |
| `RTO-NET-06` | Preserve explicit, reviewable network boundaries without claiming measured runtime capacity. |

Authoritative references: `RTO_NET.md` (`RTO-NET-01` through
`RTO-NET-06`), `docs/06_AWS/01`, `docs/06_AWS/02`, `docs/06_AWS/04`,
`docs/08_Seguridad/04`, and `docs/13_Pruebas/01`. These sources are cited
without reproducing or amending the ignored `docs/` source of truth.

## Verification behavior

`tests/test_dev_network_boundaries.py` and
`tests/test_network_security_group_boundaries.py` inspect the Terraform source
and fail when an allowed hop loses its least-privilege source reference or a
denied route, resource, CIDR, protocol, public address, or attachment appears.
The checks include the DEV root modules as well as reusable network modules.

This is configuration evidence only. It does not prove deployed security-group
state, packet reachability, AWS availability, or runtime isolation.

## Exclusions and authorization

- No Terraform plan against an AWS backend and no `terraform apply`.
- No AWS resource mutation and no QA or PROD work.
- No claim of deployed ALB, gateway, BFF, service, broker, database, NAT,
  endpoint, peering, TGW, or VPN behavior.
- No AWS runtime or packet-path check was authorized or run.
- No `docs/` source-of-truth file was changed.

## Validation evidence

| Check | Result | Evidence |
|---|---|---|
| Targeted boundary tests | PASS | `python3 -m unittest tests.test_dev_network_boundaries tests.test_network_security_group_boundaries -v` ran 14 tests; all passed in this review. |
| Full Python test discovery | PASS | `python3 -m unittest discover -s tests -v` ran 53 tests; all passed in this review. |
| Terraform formatting | PASS | `terraform fmt -check -recursive infra/accounts/sumak-dev/us-east-1/dev/network infra/accounts/sumak-dev/us-east-1/dev/network-boundaries infra/modules/network-security-groups` exited 0. |
| Network stack backend-free init and validation | PASS | Both DEV roots initialized with `terraform init -backend=false -input=false -lockfile=readonly` using isolated `TF_DATA_DIR` under `/tmp/opencode`, then `terraform validate -no-color` succeeded. No backend access or AWS mutation. |
| Diff whitespace validation | PASS | `git diff --check` exited 0. |
| AWS runtime and packet-path behavior | NOT_RUN | Outside this configuration-verification scope; no runtime evidence is claimed. |

Unit, architecture, integration, contract, security-runtime, and load/stress
gates are not applicable to these repository-local static Terraform checks.

## Documentation impact

Adds tracked configuration-verification evidence and records the
instructor-provided reference project's non-authoritative role in `AGENTS.md`.
No `docs/` source-of-truth content is changed.
