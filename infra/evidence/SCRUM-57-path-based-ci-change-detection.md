# SCRUM-57 Path-based CI change detection

## Scope and usage

The PR-validation routing script maps changed Gradle component inputs to component `:check` tasks, shared Gradle dependency inputs to repository-wide `check`, Terraform changes under account/module trees to Terraform validation, and contract sources to only explicitly configured Gradle consumers. Add contract consumer mappings to `config/ci/path-routing.json` only when an authoritative mapping is established. Missing or invalid consumers deliberately fail as `BLOCKED`; do not guess a consumer.

Workflows call `scripts/ci/detect_changes.py --base "$BASE_SHA" --head "$HEAD_SHA" --github-output "$GITHUB_OUTPUT"`. The script includes deleted paths in its Git diff filter, emits named outputs, and returns nonzero for unresolved contract mappings. The PR Terraform and general validation jobs use `if: always()` so they are scheduled after routing fails; each has a final always-run routing assertion that fails `BLOCKED` unless the routing job result is `success` and required outputs are exactly `true` or `false`, rejecting empty/default values even if routing emitted outputs before failure. Terraform-specific steps, including credentialed plan and artifact upload, run only when routing succeeded and `terraform_changed == 'true'`. Contract and Gradle steps run only when routing succeeded and their respective outputs are `true`; the final assertion requires their outcome to be `success` for true and `skipped` for false. General validation steps such as wrapper validation, PR metadata validation, and policy tests continue independently of routing.

## Validation evidence

Commit: working tree (uncommitted); no commit SHA available. Dataset: synthetic temporary Gradle project, route configuration, and mocked Git diff. Environment: local Linux workspace; no AWS account, OCI image, database, or contract package involved. Timestamp: 2026-11-28.

| Gate | State | Evidence / reason |
|---|---|---|
| Unit | PASS | Focused and full test commands below passed. Routing tests cover direct component, shared Gradle, recursive Terraform, explicit consumer, missing/invalid mapping, deletion filter, and workflow outputs/failure; policy tests cover the scheduling, gating, and fail-closed workflow behavior. |
| Architecture | NOT_RUN | This Python workflow-routing utility does not implement service/domain architecture or Java package boundaries; ArchUnit is inapplicable. |
| Integration | NOT_RUN | No database, migrations, brokers, or service adapter is touched. Workflow wiring is exercised by unit tests against the script entry point and output file. |
| Contract | NOT_RUN | No contract artifact is compiled or modified; routing of a synthetic contract path is covered by unit tests. |
| Security | NOT_RUN | No auth, secrets, PII, dependency graph, or deployable artifact changes are exercised by this bounded feature. Security scanning infrastructure remains separate. |
| Load/Stress | NOT_RUN | This deterministic CI path router has no service capacity objective; no performance claim is made. |

YAML parse validation: PASS — `ruby -e 'require "yaml"; ARGV.each { |path| YAML.load_file(path); puts "YAML_PARSE_PASS #{path}" }' .github/workflows/pr-validation.yml .github/workflows/security-scanning.yml` printed `YAML_PARSE_PASS` for both workflow files.

Final test validation:

- `python3 -m unittest tests.test_pr_validation_terraform_job tests.test_security_scanning_policy tests.test_ci_path_routing -v` — PASS, 22 tests.
- `python3 -m unittest discover -s tests -v` — PASS, 116 tests.
- `git diff --check` — PASS.
- `python3 -m py_compile scripts/ci/detect_changes.py` — PASS (exit 0; no output).
- Ruby YAML parser command above — PASS for both workflows.

Initial unit run exposed a test-fixture issue: the test used `build.gradle`, which is correctly classified as a shared dependency input and therefore routes to `check`. The test was corrected to use a component source path; no production behavior or assertion was weakened. The focused policy tests now cover route-job failure despite emitted outputs, empty/default and invalid boolean outputs, contract/Gradle step success versus skipped outcomes for true/false, route-result guards preventing those steps from running after failure, and unrelated mandatory validation. No further core implementation correction was required.

Diff hygiene: `git diff --check` passed. Terraform-specific formatting/init/validate/security scanning and credentialed plans/uploads are gated on successful `terraform_changed == true` routing. The mandatory Terraform job and general validation job still run after routing failure and end in explicit fail-closed routing assertions; general checks unrelated to route outputs continue. AWS account guard and non-apply assertions remain covered. No routing implementation change was needed. No ignored `docs/`, SCRUM-58, Helm, deployment, QA/PROD, or AWS configuration was changed.
