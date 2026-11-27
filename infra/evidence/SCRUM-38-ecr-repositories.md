# SCRUM-38 — DEV ECR repository evidence

## Bounded scope

- Environment: DEV only
- Region: `us-east-1`
- Artifact: `identity-svc`
- Repository: `sumak/dev/identity-svc`
- Management: Terraform with the SCRUM-37 same-account S3 backend

No QA/PROD repository, cross-account policy, replication, permanent credential,
or assumed `LabRole` push permission is included.

## Configuration evidence

| Check | Status | Evidence |
|---|---|---|
| Terraform formatting | PASS | `terraform fmt -check -recursive` completed with no findings. |
| Terraform validation | PASS | `terraform validate` succeeded with AWS provider 6.74.0. |
| Reviewed Terraform plan | PASS | Remote S3 backend initialized; plan: 2 to add, 0 to change, 0 to destroy. Saved outside Git at `/tmp/opencode/scrum-38.tfplan`. |
| Private repository with immutable tags | PASS | Terraform apply created `sumak/dev/identity-svc`; AWS ECR describe confirmed `IMMUTABLE`. |
| Scan on push and AES256 encryption | PASS | AWS ECR describe confirmed scan-on-push and AES256 encryption. |
| Post-apply drift check | PASS | `terraform plan -detailed-exitcode` returned 0 with no changes. |
| Authorized image push | BLOCKED_ARTIFACT | `identity-svc` has no Dockerfile or other OCI packaging definition; no substitute image was pushed. |
| Read-identity pull and digest verification | BLOCKED_ARTIFACT | No legitimate `identity-svc` image digest exists to pull. |
| Container recovery by digest | BLOCKED_ARTIFACT | Requires the separately defined build artifact and its immutable digest. |

## Runtime evidence record

Terraform apply completed in the DEV account with 2 resources added, 0 changed,
and 0 destroyed. Complete the image fields after `identity-svc` gains reviewed
OCI packaging:

- Source revision:
- Authorized push principal:
- Image digest:
- Push timestamp (UTC):
- Read identity:
- Pull verification:
- Recovery verification:
- Reviewed plan/apply reference: 2 added, 0 changed, 0 destroyed; post-apply plan returned no changes.

Terraform declarations and screenshots do not establish runtime success. Keep
unexecuted checks as `NOT_RUN` or `PENDING`; use `BLOCKED_ARTIFACT` only when a
required build artifact does not exist, and record permission blockers without
bypassing them.
