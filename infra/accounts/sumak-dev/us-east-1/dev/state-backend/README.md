# SCRUM-37 — Terraform S3 Backend Bootstrap & Operations

**Branch/Key:** `feat/SCRUM-37-bootstrap-dev-terraform-s3-backend-and-state-locking`
**Account:** `****9751` (redacted, us-east-1, same-account DEV)
**Purpose:** Safe bootstrap, init/plan/apply guidance, recovery, and lock troubleshooting for the SUMAK DEV Terraform state backend.

**UTC Evidence Window:** 2026-11-24 02:34 UTC (all remote operations completed successfully)

---
## 1. Safe Bootstrap / Adoption

The account-specific S3 bucket declared in `versions.tf` was manually bootstrapped through AWS MCP with the following settings:

- Versioning enabled
- AES256 SSE-S3 encryption
- All public access blocked (BlockPublicAcls, BlockPublicPolicy, IgnorePublicAcls, RestrictPublicBuckets)
- BucketOwnerEnforced ownership controls
- TLS-only IAM policy (DenyInsecureTransport)
- Backend configuration with native S3 locking (`use_lockfile = true`)

**Do not** recreate the bucket. The `import` block in `main.tf` adopts the existing bucket into the module resource. If the bucket is ever lost, engage the AWS restoration process before re-attempting Terraform operations.

The module uses `awscc_s3_bucket` because the Learner Lab SCP denies
`s3:GetBucketObjectLockConfiguration`, which prevents the standard AWS provider
from refreshing an imported `aws_s3_bucket`. Cloud Control adoption was
validated and does not bypass that SCP boundary.

---
## 2. Initialization Workflow

Remote `terraform init` with profile academy succeeded. To run locally with valid credentials:

```bash
# 1. Verify the temporary caller belongs to the expected DEV account
aws sts get-caller-identity

# 2. Initialize the backend
terraform init

# 3. Create and review a saved plan
terraform plan -out=scrum-37.tfplan

# 4. Apply the reviewed plan only after explicit approval
terraform apply scrum-37.tfplan
```

**Never run `terraform init` or `terraform apply` without confirmed valid AWS credentials.** In this environment, `init -backend=false` and `validate` pass; remote init with profile academy is fully supported.

---
## 3. Plan / Apply Approval

- `terraform plan` always required before `terraform apply`.
- Remote `plan`/`apply` completed successfully with profile academy (1 imported, 1 added, 0 changed, 0 destroyed).
- The first plan imported the bucket through `awscc_s3_bucket` and reconciled its independently managed settings. Review every action; do not assume a no-op.
- Never bypass plan review; the S3 state bucket is infrastructure-critical.

---
## 4. Recovery / Version Restore

If state corruption is suspected:

1. **Do not delete `.tflock` or the state file** until you confirm no active Terraform writer.
2. Run `terraform state pull` and preserve the current state as a recovery copy.
3. Identify the required prior object version in S3 and download it to a protected temporary path.
4. Verify the selected version's checksum, metadata, account, bucket, and key.
5. If a lock is stuck, resolve it per Section 5 before proceeding.
6. With explicit approval, restore via `terraform state push` and immediately run a reviewed `terraform plan` to detect drift.

---
## 5. Lock Troubleshooting

The `.tflock` file is stored in the S3 bucket under the key path `us-east-1/dev/state-backend/terraform.tfstate.tflock`.

**Symptoms and resolution:**

| Symptom | Resolution |
|---------|------------|
| `Error: Error acquiring the lock` | Run `terraform force-unlock <lock-id>` only after confirming no other Terraform process is active. |
| Stale `.tflock` after crash | Confirm the owning process is gone, preserve the lock metadata as evidence, then run `terraform force-unlock <lock-id>` if approved. Native S3 locks have no assumed TTL. |
| Put/Head/Delete test confirms lock-object permissions | This test validates IAM permissions but is **not** a real concurrent Terraform lock test. Do not rely on it for multi-user concurrency. |
| Lock persists after `terraform apply` completes | Verify no other terminal is running `terraform plan` or `terraform apply`. If clear, force-unlock as above. |

**Key principle:** The Put/Head/Delete operations confirmed the bucket allows the expected lock interactions, but this is **not** a substitute for a real concurrent Terraform lock test. Always assume multiple writers can conflict.

---
## 6. Version Restore from S3 Versioning

The bucket has versioning enabled. To restore a prior state version:

```bash
# Set this from the reviewed environment configuration; do not paste credentials.
STATE_BUCKET="sumak-dev-tfstate-<account-id>-us-east-1"
STATE_KEY="us-east-1/dev/state-backend/terraform.tfstate"

# Preserve the current state before recovery.
terraform state pull > /tmp/opencode/scrum-37-current.tfstate

# List prior versions (requires authorized temporary AWS credentials).
aws s3api list-object-versions \
    --bucket "${STATE_BUCKET}" \
    --prefix "${STATE_KEY}"

# Download the approved version, verify it, then restore only with approval.
aws s3api get-object \
    --bucket "${STATE_BUCKET}" \
    --key "${STATE_KEY}" \
    --version-id '<version-id>' \
    /tmp/opencode/scrum-37-recovery.tfstate
terraform state push /tmp/opencode/scrum-37-recovery.tfstate
terraform plan
```

---
## 7. Validation Summary

```bash
# Local validation:
terraform validate              # PASS (AWS provider 6.74.0)
terraform fmt -check -recursive # PASS

# Remote Terraform operations completed successfully with profile academy:
terraform init                  # PASS - backend init with S3
terraform plan                  # PASS - 1 imported, 1 added, 0 changed, 0 destroy
terraform apply                 # PASS - 1 imported, 1 added, 0 changed, 0 destroyed

# Post-apply validation
terraform plan -detailed-exitcode  # returned 0 No changes (no drift)
```

---
**No secrets (keys, secrets, passwords) are included in this document.**
**Account identifiers in this runbook are redacted; use the reviewed Terraform configuration as the source of the bucket name.**
**Branch/key `feat/SCRUM-37-bootstrap-dev-terraform-s3-backend-and-state-locking` is the active work key.**
**UTC evidence window: 2026-11-24 02:34 UTC.**
