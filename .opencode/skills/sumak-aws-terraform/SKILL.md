---
name: sumak-aws-terraform
description: Implement SUMAK Terraform, Learner Lab networking, EKS, ECR, bastion, and Helm changes within documented limits
---

## Infrastructure rules

- The generic `academy` profile no longer exists. Select the destination account explicitly for every Terraform or AWS CLI command with `--profile <profile>` or `var.aws_profile`; use only profiles registered in `infra/accounts-map.yaml`.
- Before `terraform plan`, `terraform apply`, or any AWS write, run `aws sts get-caller-identity --profile <profile>`. Continue only when the temporary session is valid and the returned AccountId exactly matches the assigned `accountId` in `infra/accounts-map.yaml`.
- If STS fails, the AccountId differs, or the account is `PENDING_ASSIGNMENT`, stop and ask the user to run `aws-academy <profile>`. Repeat STS verification afterward; never expose or persist the temporary credentials.
- Keep reusable Terraform under `infra/modules/` and account/region/environment roots under `infra/accounts/`. Never mix DEV, QA, and PROD state, credentials, data, or secrets.
- Use a private, versioned, encrypted S3 backend in the same account with native `use_lockfile = true` only after permissions are verified. Never commit state or plan files.
- Build a non-overlapping VPC across three planned AZs with public ingress subnets, private application/EKS subnets, and private data subnets. Databases, brokers, caches, search, pods, and services have no public endpoints.
- Prefer SSM Session Manager for a private bastion. Never allow public SSH or `0.0.0.0/0` administration.
- Put ALB/TLS in front of the logical Spring gateway. Treat Amazon API Gateway as an explicit PoC/ADR, not a reason to add business REST or duplicate the gateway.
- EKS control plane, node groups, ASG, instance sizes, and replicas must remain inside verified Learner Lab permissions and quotas: at most 9 running EC2 per account, 32 EC2 vCPU per region, EC2 no larger than `large`, and no invented IAM roles, cross-account access, or IRSA.
- Store OCI images in per-environment ECR repositories and deploy immutable approved digests. Do not assume `LabRole` can push or that cross-account replication exists.
- Helm charts require startup/readiness/liveness probes, requests/limits, secret references, graceful shutdown, and bounded rollout/rollback settings.

Run `terraform fmt`, `validate`, security/policy checks, and reviewed `plan` before any authorized apply. Record real permission or capacity blockers instead of bypassing them.
