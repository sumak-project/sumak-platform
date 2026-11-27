# SCRUM-31 — Private DEV SSM bastion

This stack provisions one on-demand management instance in the first DEV
private application subnet. It has no public IPv4 address, no inbound
security-group rules, and no SSH access. Session Manager reaches the agent
through three private VPC interface endpoints; the stack creates no NAT
gateway or public administration path.

## Before planning

1. Run `aws-academy sumak-dev`, then verify
   `aws sts get-caller-identity --profile sumak-dev` resolves to the assigned
   account in `infra/accounts-map.yaml`.
2. Verify that `LabInstanceProfile` exists and permits the managed instance to
   register with Systems Manager. Do not create a replacement IAM role.
3. Query the DEV account for all running EC2 instances and their regional vCPU
   total. Pass the observed counts as variables:

   ```bash
   terraform plan \
     -var='existing_running_ec2_count=<observed-count>' \
     -var='existing_running_vcpu_count=<observed-vcpus>'
   ```

The module refuses a plan that would exceed nine running EC2 instances in the
account or 32 EC2 vCPUs in `us-east-1`. Counts in a saved plan become stale;
refresh them again immediately before an authorized apply.

## Validation and access

Run `terraform fmt -check -recursive`, `terraform init`, `terraform validate`,
and review the complete plan. An apply requires explicit approval and verified
VPC endpoint, EC2, SSM, and instance-profile permissions.

After an approved apply, verify the instance has no public IP and is registered
as an SSM managed node. Start a temporary port-forwarding session for an
explicitly authorized private target; for PostgreSQL, point DBeaver at the
local forwarded port. Terminate the session after use and retain sanitized
Session Manager/CloudTrail evidence. Never expose port 22 or store database
credentials in Terraform, Git, shell history, or the instance.

Runtime evidence is recorded in
`infra/evidence/SCRUM-31-private-ssm-bastion.md`. The SSM API session lifecycle
was exercised, but local interactive-console operation and unauthorized or
revoked identity denial remain `NOT_RUN`. The live service-quota lookup remains
`BLOCKED_AWS_PERMISSION`; observed usage against documented project boundaries
is not live quota proof. Do not bypass these limitations with public SSH.
