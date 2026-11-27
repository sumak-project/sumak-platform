# SCRUM-33 — DEV VPC and three-AZ subnet layout

This stack provisions the `sumak-dev` VPC in `us-east-1` with the user-approved
CIDR `10.10.0.0/16`.

| Account zone name | Physical AZ ID | Public ingress | Private application | Private data |
|---|---|---|---|---|
| `us-east-1a` | `use1-az2` | `10.10.0.0/20` | `10.10.64.0/20` | `10.10.128.0/20` |
| `us-east-1b` | `use1-az4` | `10.10.16.0/20` | `10.10.80.0/20` | `10.10.144.0/20` |
| `us-east-1c` | `use1-az6` | `10.10.32.0/20` | `10.10.96.0/20` | `10.10.160.0/20` |

The AZ mapping was observed from the DEV account before planning. Zone names
can differ between accounts; the physical IDs are the deployment boundary.

## Routing boundary

Each of the nine subnets has a dedicated route table. Only public ingress
subnets receive `0.0.0.0/0` through the Internet gateway and automatic public
IPv4 assignment. Application and data subnets have neither setting.

NAT gateways and private AWS endpoints remain deferred until permissions,
cost, and required egress flows are reviewed. Consequently, this ticket does
not claim private workload Internet access, high availability, Multi-AZ data
services, or runtime readiness.

## Validation and deployment

With valid temporary DEV credentials:

```bash
terraform init
terraform fmt -check -recursive
terraform validate
terraform plan -out=scrum-33.tfplan
```

Terraform initializes the SCRUM-37 same-account encrypted, versioned S3
backend at state key `us-east-1/dev/network/terraform.tfstate`, using native
`use_lockfile = true` locking and the temporary `academy` profile. Remote
backend initialization succeeded for SCRUM-33. No state contents or credentials
are included in this evidence.

Review the saved plan before any apply. Terraform state and plan files must
never be committed; the SCRUM-33 plan remains `/tmp`-only and uncommitted.
Apply requires explicit human approval. After an approved
apply, verify the VPC, all nine subnets, their physical AZ IDs, route-table
associations, and the absence of Internet routes in both private tiers.
