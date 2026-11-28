# SCRUM-124 QA promotion orchestration evidence

## Scope

This ticket implements non-mutating pull-request orchestration from `dev` to
`qa`. It serializes promotion runs, rejects stale source or target branches,
binds the reviewed PR to an exact commit and OCI digest, downloads an
exact-SHA evidence artifact, validates all six mandatory gates, and requests
protected owner approval only after gate validation.

The workflow does not copy images, call AWS, deploy workloads, run smoke tests,
perform rollback, configure branch/environment protection, merge a PR, or
enable QA-to-PROD promotion.

## Local validation context

- Base commit: `b350cd30c503cd9ab2ed37e9fe3d87b90f700637`
- Branch: `feat/SCRUM-124-qa-promotion-orchestration`
- Environment: local Linux workspace
- Executed at: `2026-11-28T14:28:17Z`
- Dataset: synthetic promotion evidence and static workflow-policy fixtures
- OCI image / AWS account / QA runtime: not used

The final immutable head commit and GitHub Actions run links are recorded in
Jira after PR execution. Local static and unit validation does not prove that a
DEV-to-QA promotion occurred.

## Commands and observed results

| Command | Result |
|---|---|
| `python3 -m unittest tests.test_validate_promotion tests.test_qa_promotion_workflow -v` | PASS — 27 tests |
| `python3 -m unittest discover -s tests -v` | PASS — 137 tests |
| `./gradlew check --no-daemon` | PASS — build successful; 106 actionable tasks, 28 executed and 78 up-to-date |
| `python3 config/quality-gates/validate_promotion.py --policy-only` | PASS — canonical six-gate policy |
| `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/qa-promotion-gate.yml"); puts "YAML_PARSE_PASS .github/workflows/qa-promotion-gate.yml"'` | PASS |
| `git diff --check` | PASS |

## Fail-closed controls exercised by tests

- only a same-repository `dev` to `qa` pull request is accepted;
- draft, stale-source, stale-target, fork, malformed metadata, and mismatched
  commit/digest cases block;
- missing, duplicate, expired, or wrong-SHA evidence artifacts block;
- all six gates still require `PASS` while manual approval is pending;
- default validator behavior still requires complete approval evidence;
- protected approval follows gate validation;
- both `dev` and `qa` tips are rechecked after approval;
- the workflow has read-only permissions and never merges or deploys.

## Six-gate classification for this bounded ticket

| Gate | Status | Evidence / limitation |
|---|---|---|
| Unit | PASS | The focused 27-test suite and full 137-test repository suite passed. |
| Architecture | PASS | `./gradlew check --no-daemon` executed architecture-boundary checks successfully. |
| Integration | NOT_RUN | No QA runtime, database, broker, migration, or service adapter was exercised. |
| Contract | NOT_RUN | No official contract compiler suite was executed for this workflow-only change. |
| Security | NOT_RUN | Protected CI security scanning remains pending until the PR runs. |
| Load/Stress | NOT_RUN | No deployed workload or authorized load target exists. |

These ticket-level `NOT_RUN` values are not promotion evidence. The
orchestration workflow blocks DEV-to-QA promotion until an exact-SHA artifact
contains `PASS` evidence for all six mandatory gates.

## Operational references and current blockers

- Workflow: `.github/workflows/qa-promotion-gate.yml`
- Policy and procedure: `config/quality-gates/README.md`
- Validator: `config/quality-gates/validate_promotion.py`
- Required artifact name: `promotion-evidence-<40-character-dev-SHA>`
- Required artifact file: `promotion-evidence.json`
- Required PR metadata: `Promotion-Commit` and `Artifact-Digest`

The evidence producer, verified GitHub environment protection, QA branch
protection, QA deployment, smoke tests, rollback, and AWS permissions are
separate prerequisites. Until they are implemented and evidenced, actual
promotion remains `NOT_RUN`.

No ignored `docs/` content was edited.
