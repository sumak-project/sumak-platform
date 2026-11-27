# SCRUM-34 — DEV route tables and private boundaries

This stack documents the route-boundary design for the `sumak-dev` VPC in
`us-east-1`. The authoritative network root is
`../network/main.tf`; its VPC is `10.10.0.0/16`, with these physical
Availability Zone IDs and subnet CIDRs:

| Account AZ name | Physical AZ ID | Public ingress | Private application | Private data |
|---|---|---|---|---|
| `us-east-1a` | `use1-az2` | `10.10.0.0/20` | `10.10.64.0/20` | `10.10.128.0/20` |
| `us-east-1b` | `use1-az4` | `10.10.16.0/20` | `10.10.80.0/20` | `10.10.144.0/20` |
| `us-east-1c` | `use1-az6` | `10.10.32.0/20` | `10.10.96.0/20` | `10.10.160.0/20` |

## Route policy

Each subnet has its own route table and explicit subnet association. Only the
three public-ingress route tables may have `0.0.0.0/0` routed through the VPC's
Internet Gateway (IGW). The application and data route tables retain only the
local VPC route; they have no IGW route and do not assign public IPv4 addresses.
The IGW is public-ingress-only, not a private egress path.

No VPC peering, Transit Gateway, VPN, or cross-environment connectivity is
included. NAT gateways and private AWS endpoints are deferred pending concrete
egress requirements, permissions, and cost review. Do not infer private Internet
access, service availability, or runtime readiness from this design.

## Validation commands

From this directory, after confirming the execution environment and credentials
are appropriate:

```bash
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

Initialization with `-backend=false` is for local configuration validation; it
does not initialize the configured remote state backend. No plan or apply is
authorized by this ticket. Any deployment requires a separately reviewed plan
and explicit human authorization.

## Documentation impact

This README records the route-table and subnet-tier boundary for the existing
network root. No `docs/` source-of-truth files are changed.

## Authoritative references

- `RTO_NET.md`: `RTO-NET-01`, `RTO-NET-02`, `RTO-NET-05`.
- `RTO_IAC.md`: `RTO-IAC-01`, `RTO-IAC-02`, `RTO-IAC-03`, `RTO-IAC-04`,
  `RTO-IAC-06`.
- `docs/06_AWS/01`, `docs/06_AWS/03`, `docs/06_AWS/04`.
- `docs/08_Seguridad/01`.
- `docs/00_Gobierno/03`.
