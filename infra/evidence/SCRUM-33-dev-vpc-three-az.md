# SCRUM-33 — DEV VPC and three-AZ evidence

## Bounded scope

- Account/environment: `sumak-dev` / DEV
- Region: `us-east-1`
- VPC CIDR: `10.10.0.0/16` (explicitly approved for this ticket)
- Physical AZ IDs: `use1-az2`, `use1-az4`, `use1-az6`
- Layout: three public ingress, three private application, and three private
  data subnets
- Private egress: deferred; no NAT gateway or VPC endpoints

No EKS, ALB, RDS, broker, cache, search, peering, transit gateway, VPN, QA, or
PROD resource is included. A three-AZ subnet layout is not evidence of service
high availability or Multi-AZ data deployment.

## Validation evidence

| Check | Status | Evidence |
|---|---|---|
| Physical AZ discovery | PASS | AWS EC2 API returned the three selected name/ID mappings as available in the DEV account. |
| Terraform formatting | PASS | `terraform fmt -check -recursive` completed with no findings. |
| Terraform validation | PASS | `terraform validate` succeeded with AWS provider 6.74.0. |
| Static network policy tests | PASS | Full Python suite passed 25/25 checks, including five SCRUM-33 topology boundaries. |
| Reviewed Terraform plan | PASS | Remote backend initialized; plan: 32 to add, 0 to change, 0 to destroy. Saved outside Git at `/tmp/opencode/scrum-33.tfplan`. |
| VPC and nine-subnet deployment | PASS | Authorized apply created 32 resources: 1 VPC, 1 IGW, 9 subnets, 9 route tables, 9 associations, and 3 public routes; 0 changed and 0 destroyed. |
| Physical subnet placement | PASS | AWS EC2 API confirmed all nine CIDRs in the selected physical AZ IDs; public IPv4 mapping is true only for the three public subnets. |
| Private route isolation | PASS | AWS EC2 API confirmed all six application/data route tables contain only the local VPC route. |
| Public ingress routing | PASS | AWS EC2 API confirmed each public subnet has its own route table and `0.0.0.0/0` route to the managed IGW. |
| Post-apply drift check | PASS | `terraform plan -detailed-exitcode` returned 0 with no changes. |
| NAT/private endpoint decision | DEFERRED | Permission, cost, and concrete private egress requirements are not approved. |

Do not convert `NOT_RUN`, `PENDING`, or `DEFERRED` into `PASS` from Terraform
source or screenshots alone. Record exact AWS permission or quota errors rather
than bypassing them.
