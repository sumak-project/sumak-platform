# SCRUM-49 Manual QA Promotion Approval

**Implementation status:** CONFIGURED

**QA promotion execution:** NOT_RUN

## Bounded change

The reusable QA promotion workflow now separates mandatory quality-gate
validation from human authorization. The `manual-qa-approval` job can start
only after `mandatory-quality-gates` succeeds and targets the protected
`qa-promotion-approval` GitHub environment.

The versioned promotion evidence requires an explicit `APPROVED` decision,
approver identity, UTC approval timestamp, and approval evidence reference.
Missing or invalid approval evidence blocks promotion.

## Repository environment protection

The user confirms that required reviewers are configured for the
`qa-promotion-approval` GitHub environment. This configuration was not
independently verified through the available GitHub API tooling. The workflow
declaration selects the environment; enforcement depends on that repository
setting and cannot be established by tracked workflow YAML alone.

This confirmation concerns approval protection only; it does not authorize or
execute a promotion.

## Validation

Run the dependency-free validator tests:

```bash
python3 -m unittest discover -s tests -v
```

Validate a completed evidence record:

```bash
python3 config/quality-gates/validate_promotion.py <evidence.json>
```

Actual DEV-to-QA promotion remains `NOT_RUN`. QA is not configured, deployed,
or active. The outstanding evidence and blockers are recorded in:

- `infra/evidence/SCRUM-29-environment-evidence-checklist.md`
- `infra/evidence/SCRUM-26-architecture-decisions-and-blockers.md`
- `infra/evidence/SCRUM-35-acm-dns-tls-poc.md`
- `infra/evidence/SCRUM-36-dev-application-load-balancer.md`
- `infra/evidence/SCRUM-38-ecr-repositories.md`

No AWS apply, deployment, artifact publication, or QA runtime validation is
part of SCRUM-49.
