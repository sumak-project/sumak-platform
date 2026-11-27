# DEV application load balancer

This stack configures the DEV-only public ALB, its private logical-gateway
target group, health checks, connection draining, and WSS-compatible idle
timeout. It consumes the public subnet map and ALB security group from the
`network-boundaries` remote state.

## Current limitation

SCRUM-35 found no authorized domain, hosted zone, or ACM certificate. Therefore
`enable_https_listener` remains `false`, DNS/WAF resources are excluded, and
TLS, WSS, health, and origin-protection runtime evidence remains `NOT_RUN` /
`BLOCKED_EXTERNAL_DEPENDENCY`. Do not invent a certificate ARN.

If any AWS account other than the currently active DEV account is required,
ask the user to activate access first; normally only AWS DEV access is enabled.

## Validation

Run `terraform fmt -check -recursive`, `terraform init -backend=false`, and
`terraform validate`. A plan or apply requires separate authorization and the
missing TLS dependency must be resolved before enabling the listener.
