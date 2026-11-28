# SCRUM-143 six-gate PR validation evidence

## Scope

This change defines the machine-readable six-gate policy and fail-closed
validation semantics used by pull requests targeting `dev` and future
DEV-to-QA promotion evidence. It does not deploy to QA, change GitHub branch or
environment protection, mutate AWS, or enable QA-to-PROD promotion.

The policy requires `PASS` for `unit`, `architecture`, `integration`,
`contract`, `security`, and `load_stress`. Missing, malformed, failed,
pending, skipped, cancelled, blocked, `NOT_RUN`, and waived gate evidence
blocks promotion. A documented waiver remains evidence of a waiver, not a
passing mandatory gate.

## Local validation context

- Base commit: `57e6bbb9bb497e4566e121ba27cc7896c4b1bb94`
- Branch: `feat/SCRUM-143-six-gate-pr-validation`
- Environment: local Linux workspace
- Executed at: `2026-11-28T14:17:20Z`
- Dataset: repository policy fixtures and synthetic invalid evidence documents
- OCI image / AWS account / database: not applicable; no image was built and no
  cloud or database operation was authorized

The final immutable head commit and GitHub Actions run links must be added to
Jira after the PR executes. This local record does not substitute for CI.

## Commands and observed results

| Command | Result |
|---|---|
| `python3 -m unittest tests.test_validate_promotion -v` | PASS — 16 tests |
| `python3 -m unittest discover -s tests -v` | PASS — 126 tests |
| `python3 config/quality-gates/validate_promotion.py --policy-only` | PASS — canonical six gates, `PASS` required, target `dev` |
| `./gradlew check --no-daemon` | PASS — build successful; 106 actionable tasks, 28 executed and 78 up-to-date |
| `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/pr-validation.yml"); puts "YAML_PARSE_PASS .github/workflows/pr-validation.yml"'` | PASS |
| `git diff --check` | PASS |

An earlier full Python run failed because an existing workflow-policy test
expected the stable step name `Test quality gate policy`. The workflow retained
that required name, the full suite was rerun, and all 126 tests passed. The
failed run is not represented as a passing result.

## Six-gate evidence classification for this bounded change

| Gate | Status | Evidence / limitation |
|---|---|---|
| Unit | PASS | The focused 16-test validator suite and full 126-test repository suite passed. |
| Architecture | PASS | `./gradlew check --no-daemon` executed the repository architecture-boundary tasks and completed successfully. |
| Integration | NOT_RUN | No QA runtime, database, broker, migration, or service-adapter integration was in scope or available. |
| Contract | NOT_RUN | Policy fixtures were tested, but official contract compiler validation was not executed and is not claimed. |
| Security | NOT_RUN | Repository security scanners execute in protected CI; no local scanner result is claimed here. |
| Load/Stress | NOT_RUN | No authorized deployed workload or capacity objective exists for this policy-only change. |

The `NOT_RUN` rows above are truthful ticket-level classifications. They cannot
be used as DEV-to-QA promotion evidence: the promotion validator requires all
six mandatory gates to be `PASS`.

## Operational use

- Policy: `config/quality-gates/gate-policy.json`
- Validator: `config/quality-gates/validate_promotion.py`
- Evidence template: `config/quality-gates/promotion-evidence.template.json`
- Reproduction guide: `config/quality-gates/README.md`
- PR enforcement: `.github/workflows/pr-validation.yml`

No ignored `docs/` content was edited.
