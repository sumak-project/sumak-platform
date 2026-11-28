# Mandatory promotion quality gates

`gate-policy.json` is the machine-readable repository policy for promotions from
DEV to QA. Its canonical gates are:

1. `unit`
2. `architecture`
3. `integration`
4. `contract`
5. `security`
6. `load_stress`

Every gate must have status `PASS` and must include its executed command,
observed result, and one or more evidence references. Missing or malformed
evidence and every non-`PASS` status block promotion. In particular,
`NOT_RUN`, `PENDING`, `SKIPPED`, `CANCELLED`, `FAIL`, `BLOCKED_*`, and
`WAIVED_WITH_ADR` never become an implicit pass. A waiver can document a
decision, but it cannot satisfy a mandatory promotion gate.

Promotion evidence must identify the full lowercase 40-character Git commit
SHA and immutable OCI digest. Timestamps use second-precision ISO 8601 UTC
(`YYYY-MM-DDTHH:MM:SSZ`). Start from
`promotion-evidence.template.json`; do not replace execution evidence with a
written assertion.

Pull requests targeting `dev` run the policy validator explicitly before the
repository test suite. The workflow summary reports the canonical gates and
the required result so an invalid or incomplete policy is actionable rather
than silently skipped:

```bash
python3 config/quality-gates/validate_promotion.py --policy-only
python3 -m unittest tests.test_validate_promotion -v
```

This policy does not deploy to QA, configure GitHub environments or branch
protection, authorize AWS access, or enable a QA-to-PROD path.

## DEV-to-QA pull request orchestration

`.github/workflows/qa-promotion-gate.yml` runs only for pull requests from the
repository `dev` branch to `qa`. Promotion pull request bodies must contain
exactly one value for each field:

```text
Promotion-Commit: <40-character lowercase Git SHA>
Artifact-Digest: sha256:<64 lowercase hexadecimal characters>
```

`Promotion-Commit` must equal the reviewed PR head and the current `dev` tip.
The workflow also requires the PR base to remain the current `qa` tip. Runs are
serialized without cancelling an in-flight approval, and both branch tips are
checked again after protected environment approval so a stale run cannot
authorize a merge.

The gate job downloads exactly one non-expired Actions artifact named
`promotion-evidence-<Promotion-Commit>`. That artifact must have been produced
for the same commit and contain exactly one `promotion-evidence.json`. Every
gate must be `PASS`, and the evidence commit and OCI digest must match the PR
metadata. Missing, ambiguous, expired, malformed, mismatched, or non-passing
evidence blocks the workflow.

The `qa-promotion-approval` environment records the manual owner decision only
after evidence validation. The approval job performs no merge itself: branch
protection must require its successful check before a human-authorized merge.
This orchestration performs no AWS, deployment, smoke-test, rollback, branch
protection, or production operation.
