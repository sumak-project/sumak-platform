# DEV ECR repositories

This stack manages same-account DEV ECR repositories for approved buildable
artifacts. The reviewed DEV scope currently includes:

- `sumak/dev/identity-svc`
- `sumak/dev/config-svc` (added and exercised for SCRUM-142)

Other Gradle modules and application directories remain placeholders and must
not receive repositories until a later ticket establishes a buildable artifact
and explicitly extends the reviewed list.

## Access boundary

- Region: `us-east-1`
- Environment/account: `sumak-dev` / DEV
- Terraform profile: `sumak-dev`
- State: the SCRUM-37 encrypted, versioned same-account S3 backend
- State key: `us-east-1/dev/ecr/terraform.tfstate`

The stack defines no repository resource policy. An approved same-account
console identity must perform image pushes. Do not assume `LabRole` can push,
and do not add permanent credentials, cross-account access, replication, or
QA/PROD repositories.

## Validation and deployment

Run only with valid temporary DEV credentials:

```bash
terraform init -backend-config='profile=sumak-dev'
terraform fmt -check -recursive
terraform validate
terraform plan -out=scrum-38.tfplan
```

Review the saved plan before any apply. Plan files and Terraform state are
ignored and must never be committed. Apply requires explicit human approval.

After an approved apply, record:

1. The authorized push principal and source revision.
2. The pushed image digest (never rely on a mutable tag).
3. Pull and digest verification using the approved read identity.
4. A container recovery check from that digest.

SCRUM-142's dated execution evidence, including the exact digest, scan results,
checks, limitations, and follow-ups, is in
[`infra/evidence/SCRUM-142-ecr-digest-validation.md`](../../../../../evidence/SCRUM-142-ecr-digest-validation.md).
That evidence applies only to the recorded DEV resource and identities; it is
not authorization or validation for QA/PROD, cross-account access, or a
separate LabRole read path.
