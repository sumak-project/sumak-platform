# Private SSM bastion module

This module creates one on-demand Amazon Linux 2023 EC2 bastion in a private
application subnet. It has no public IP, no inbound security-group rules, and
no SSH listener. Administrative access is available only through AWS Systems
Manager Session Manager.

The module also creates private interface endpoints for `ssm`, `ssmmessages`,
and `ec2messages`, so the SSM agent does not require NAT or public Internet
egress. It uses the Learner Lab-provided `LabInstanceProfile` by default and
does not create or modify IAM resources.

Callers must supply observed running EC2 and vCPU counts. Preconditions stop
the plan when adding the two-vCPU bastion would exceed nine running instances
per account or 32 EC2 vCPUs in the region. These inputs must be refreshed
immediately before plan/apply; they are not runtime quota evidence by
themselves.
