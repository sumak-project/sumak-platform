# SCRUM-142 — DEV ECR digest validation evidence

**Execution date:** 2026-11-28
**Environment:** DEV, AWS account `632080579751`, `us-east-1`
**Source base revision at execution:** `0c47fc4`
**Approval/reviewer:** No reviewer approval is recorded here; see PR review state.

## Scope and infrastructure result

SCRUM-142 extended the reviewed DEV ECR artifact list to include
`sumak/dev/config-svc`, using the approved config-svc artifact from SCRUM-56.
The Terraform plan at `/tmp/opencode/scrum-142-ecr.tfplan` reported **2 add,
0 change, 0 destroy**. Apply created the repository and lifecycle policy.
Repository configuration is immutable tags, scan-on-push enabled, AES256
encryption, and retention of 30 images. No repository policy, IAM change, or
cross-account access was created. The observed repository configuration and
run-time outcomes below are not approval for broader access or environments.

The approved runtime identity is non-root `10001:10001`. The Dockerfile was
remediated to install `zlib=1.4-r0` and `expat=2.11.0-r0`.

## Identity and access chronology

The initial temporary credentials expired and the operation was recorded as
`BLOCKED_AWS_PERMISSION`. After credential renewal, STS and ECR operations
succeeded. The effective principal was
`arn:aws:sts::632080579751:assumed-role/voclabs/user5561967=ee1`; this was
**not** `LabRole`. No credential values or tokens are recorded.

## Digest and scan evidence

1. OCI index digest
   `sha256:c96b7576a08052a17b853c2de9d41b666fd1b69aa33eec25f4338102c7feded4`
   was pushed to ECR, but ECR returned `ScanNotFound` for the index. Preserve
   this as a non-approved attempt, not as a successful scan.
2. The first single-platform manifest,
   `sha256:3227dd52231482a44f79df9d8932fa5f606b0d176bc31c6e02c67233c3c91b47`,
   reached scan status `COMPLETE` but had 1 CRITICAL finding
   (`CVE-2026-4738`, zlib 1.3.2-r1) and 3 MEDIUM expat findings. It was not
   approved.
3. The final remediated image had matching source and ECR digest
   `sha256:1c7dbe50a91399e29135dab4ad4f6ee05d2b9bc5bbf5c448d98bd99978cfc897`.
   Its immutable tag is `scrum-142-0c47fc4-remediated`. ECR described the
   manifest as OCI single-platform, `ACTIVE`, with size 112519232 bytes.
   Final ECR scan status was `COMPLETE`: 0 CRITICAL, 0 HIGH, and 3 MEDIUM
   findings.

The 3 MEDIUM findings are attributed by ECR to `expat 2.10.0-r0`, although the
runtime build installs `expat 2.11.0-r0`. This version discrepancy is an open
follow-up; it is not resolved by this evidence. Do not describe the final scan
as having zero findings.

## Pull, runtime, and local validation

A real pull by the exact final digest succeeded using the same temporary
authorized principal. This establishes same-principal pull/recovery only; it
does not establish a separate consumer-role permission path.

The image was run with a read-only root filesystem, `/tmp` on tmpfs, all Linux
capabilities dropped, `no-new-privileges`, and user `10001:10001`. The
`/health/live`, `/health/ready`, and `/health/startup` endpoints each returned
`{"status":"UP"}`.

Local Trivy HIGH/CRITICAL checks reported `PASS 0` for both Alpine packages
and the JAR. The Trivy secret column was `-`; this is explicitly **not**
comprehensive secret-scan evidence.

Seven scoped tests passed: 2 OCI contract tests and 5 ECR boundary tests.
Terraform `fmt`, `init`, and `validate` passed. These results are scoped to
those executed checks; they do not assert unrun gates.

The SBOM was generated at
`/tmp/opencode/SCRUM-142-config-svc-sbom.cdx.json` (untracked), with SHA-256
`3557c1f4fddff92306bb665d9f368f16fdae35110e1fc41e3a0a575a72055e3c`.
The file is outside the repository and is not included with this tracked
evidence.

## Reproduction record

The following commands describe the executed validation sequence. Run AWS CLI
commands explicitly with the authorized, temporary `sumak-dev` profile; do not
put credential values in command arguments, shell history, or evidence. The
Terraform backend arguments also select that profile. The temporary plan path
is intentionally outside the repository.

```bash
aws sts get-caller-identity --profile sumak-dev
terraform -chdir=infra/accounts/sumak-dev/us-east-1/dev/ecr init -backend-config='profile=sumak-dev'
terraform -chdir=infra/accounts/sumak-dev/us-east-1/dev/ecr fmt -check -recursive
terraform -chdir=infra/accounts/sumak-dev/us-east-1/dev/ecr validate
terraform -chdir=infra/accounts/sumak-dev/us-east-1/dev/ecr plan -out=/tmp/opencode/scrum-142-ecr.tfplan
terraform -chdir=infra/accounts/sumak-dev/us-east-1/dev/ecr apply /tmp/opencode/scrum-142-ecr.tfplan
aws ecr describe-images --profile sumak-dev --region us-east-1 --repository-name sumak/dev/config-svc
aws ecr describe-image-scan-findings --profile sumak-dev --region us-east-1 --repository-name sumak/dev/config-svc --image-id imageDigest=sha256:1c7dbe50a91399e29135dab4ad4f6ee05d2b9bc5bbf5c448d98bd99978cfc897
```

The recorded run's image scan and container checks used the specific policies
and hardening options described above; this compact command block is a
reproduction outline, not a substitute for those recorded results or a claim
that unlisted tooling was run. For the digest-pull check, obtain ECR
authorization using the same explicitly selected profile (for example,
`aws ecr get-login-password --profile sumak-dev --region us-east-1`) and pass
it to Docker without printing or persisting the password; then pull the exact
recorded digest. The exact Terraform plan, SBOM, and other temporary outputs
are not committed.

## Status, limitations, and follow-up

- **AWS-03:** `PASS` for authorized same-account write, digest verification,
  same-principal pull, and recovery checks described here.
- **P04 separate LabRole read-path verification:** `NOT_RUN` if the
  authoritative acceptance requirement calls for that distinct identity.
  LabRole was not used to publish. Do not infer LabRole access from the
  successful `voclabs` principal pull.
- **Open:** reconcile ECR's three MEDIUM expat findings (`2.10.0-r0`) with the
  runtime's declared `2.11.0-r0`, and determine the required separate
  LabRole verification against the authoritative acceptance criterion.
- **Approval:** pending; no reviewer sign-off is evidenced.
- **Cost:** no dollar amount was measured. Only the image size stated above
  was observed.
- No QA, PROD, cross-account, or deployment activity is evidenced.
- Local validations additionally recorded for close-ticket: full Python
  discovery **96 passed**, `./gradlew check` **BUILD SUCCESSFUL**, and
  `git diff --check` passed. Integration/Contract/Load-Stress remain
  **NOT_RUN**; security evidence is limited to the scoped Trivy and ECR results
  above. Review and required CI results are recorded on the PR, not inferred
  from these local checks.
