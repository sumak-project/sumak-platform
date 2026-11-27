# SCRUM-34 — DEV route tables and private boundaries

**Status:** PLAN_ONLY
**Infrastructure change:** NOT_RUN
**Terraform plan/apply:** NOT_RUN

## Bounded scope

Describe route-table boundaries for the existing `sumak-dev` VPC in
`us-east-1`, using the three physical AZ IDs and CIDRs defined by
`infra/accounts/sumak-dev/us-east-1/dev/network/main.tf`.

| Account AZ name | Physical AZ ID | Public ingress | Private application | Private data |
|---|---|---|---|---|
| `us-east-1a` | `use1-az2` | `10.10.0.0/20` | `10.10.64.0/20` | `10.10.128.0/20` |
| `us-east-1b` | `use1-az4` | `10.10.16.0/20` | `10.10.80.0/20` | `10.10.144.0/20` |
| `us-east-1c` | `use1-az6` | `10.10.32.0/20` | `10.10.96.0/20` | `10.10.160.0/20` |

The intended design is one route table per subnet, with explicit associations.
Default Internet routing through the IGW is limited to the public-ingress
subnets. Application and data subnets are private: no IGW default route and no
public IPv4 assignment. No peering or other cross-network connectivity is
included. NAT and private endpoints remain deferred pending reviewed need,
permission, and cost.

These are configuration/design boundaries, not evidence of deployed AWS
resources or runtime isolation.

## Requirement traceability

| Reference | Bounded evidence intent |
|---|---|
| `RTO-NET-01` | Limit public routing/ingress to the public tier; keep application and data tiers private. |
| `RTO-NET-02` | Keep the public-facing path explicit and bounded; this record does not claim an ALB or runtime ingress is provisioned. |
| `RTO-NET-05` | No peering or general environment connectivity is introduced. |
| `RTO-IAC-01` | Represent the boundary as maintainable Terraform configuration. |
| `RTO-IAC-02` | Keep configuration reproducible and environment-scoped to DEV. |
| `RTO-IAC-03` | Use explicit, reviewable subnet and route-table relationships. |
| `RTO-IAC-04` | Keep infrastructure validation and deployment authorization distinct. |
| `RTO-IAC-06` | Validate the static Terraform configuration and review route-boundary behavior. |

Authoritative references: `RTO_NET.md` (`RTO-NET-01/02/05`),
`RTO_IAC.md` (`RTO-IAC-01/02/03/04/06`), `docs/06_AWS/01`,
`docs/06_AWS/03`, `docs/06_AWS/04`, `docs/08_Seguridad/01`, and
`docs/00_Gobierno/03`. The documents are cited as authority; this evidence
record does not reproduce or amend them.

## Exclusions and authorization

- No Terraform plan against an AWS backend and no `terraform apply`.
- No route, subnet, IGW, NAT, endpoint, peering, TGW, VPN, QA, or PROD changes.
- No claim of AWS runtime verification, private egress, availability, or
  production readiness.
- A reviewed plan and explicit human authorization are required before any
  deployment; this ticket grants no apply authorization.
- No `docs/` source-of-truth files are edited.

## Validation evidence

| Check | Result | Evidence |
|---|---|---|
| Terraform formatting | PASS | `terraform fmt -recursive infra/accounts/sumak-dev/us-east-1/dev/network-boundaries` followed by `terraform fmt -check -recursive infra/accounts/sumak-dev/us-east-1/dev/network-boundaries`; no differences remained. |
| Backend-free initialization | PASS | `terraform init -backend=false -input=false` succeeded from the network-boundaries directory, reusing the locked AWS provider 6.74.0 installation. No backend was initialized. |
| Terraform validation | PASS | `terraform validate` from the network-boundaries directory returned `Success! The configuration is valid.` |
| Targeted network-boundaries tests | PASS | `python3 -m unittest tests.test_dev_network_boundaries -v` ran 6 tests; all passed. |
| Full Python test discovery | PASS | `python3 -m unittest discover -s tests -v` ran 37 tests; all passed. |
| Diff whitespace validation | PASS | `git diff --check` returned exit 0. |
| AWS plan/runtime behavior | NOT_RUN | Explicitly outside this plan-only documentation evidence; no apply is authorized. |

Do not convert planned commands, source configuration, or this record into
`PASS` evidence without the corresponding command results. Provider installation
or credential limitations must be recorded as blockers; do not bypass them.

## Documentation impact

Adds tracked operational guidance and plan-only evidence adjacent to the
network-boundaries stack. No `docs/` source-of-truth content is changed.
