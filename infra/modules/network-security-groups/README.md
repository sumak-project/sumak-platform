# Network security group boundaries

This module expresses the plan-only network boundary for `SCRUM-32`. It creates
security groups and paired, security-group-referenced rules for this flow:

`reviewed origin -> ALB -> logical gateway -> mobile/admin BFF -> gRPC service -> owned database or approved broker`

The private SSM bastion has no ingress rules. It can reach only explicitly
declared private management endpoints. The module creates no VPC, subnet,
route, peering, public endpoint, compute resource, database, or broker.

## Required decisions

Callers must supply reviewed listener ports and service ownership. No numeric
port or CIDR is inferred by the module. Example CIDRs from design documents are
not reservations and must not be copied without environment review.

Only the ALB accepts CIDR-based ingress. All internal traffic uses referenced
security groups, and no security group receives default Internet egress.
Application services can reach only their owned database and explicitly
configured brokers. Topic, queue, and virtual-host authorization remains an
application/broker policy concern and is not claimed by a network rule.

## Validation status

This module is reviewable Terraform only. `terraform apply`, AWS connectivity
probes, TLS/WAF behavior, SSM sessions, availability, capacity, and production
readiness are `NOT_RUN` and outside `SCRUM-32`.

Before a future authorized use, run formatting, initialization, validation,
static security checks, and a reviewed plan. Keep the saved plan outside Git
because it may contain sensitive values. A future apply requires a separate
authorized ticket and human approval.
