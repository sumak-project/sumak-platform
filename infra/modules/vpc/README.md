# Three-AZ VPC

This module creates one environment VPC with three isolated subnet tiers in
exactly three physical availability zones:

- `public`: future ALB ingress, with public IPv4 assignment and an IGW route.
- `application`: private EKS nodes, pods, and internal services.
- `data`: private databases, brokers, caches, and search.

Every subnet receives its own route table. Application and data route tables
have no default Internet route. The module deliberately creates no NAT gateway,
VPC peering, transit gateway, VPN, public database, or cross-account resource.
Private egress and VPC endpoints require a later permission and cost decision.

Callers must provide physical AZ IDs rather than relying on account-specific
zone letters. `prevent_destroy` protects the VPC; removal requires an explicit,
reviewed lifecycle change.
