# SCRUM-53 security scanning evidence

## Implemented behavior

Pull requests targeting `dev` define separate checks for dependency
vulnerabilities, secrets in tracked history, and source/workflow security.
Scanner and action versions are pinned. Dependency review is incremental:
dependency-relevant Gradle inputs are compared between reviewed base and head.
With no such changes, the check reports an empty vulnerability delta. With
changes, it resolves every subproject's resolvable configurations into an
isolated `GRADLE_USER_HOME` and uses Trivy 0.70.0 in `rootfs` mode to inspect
cached JARs, failing on HIGH or CRITICAL findings. This avoids GitHub
dependency-graph API and repository-setting dependence.

Terraform formatting, backend-free initialization, validation, and
configuration scanning always run. Credentialed plans and uploads run only
when `*.tf` source under `infra/accounts` or `infra/modules` changes. The
initial dependency-graph API 403 and unavailable cloud credentials are
remediated CI design constraints, not PASS evidence. Local dependency
resolution populated 317 JARs. Trivy `fs` mode was rejected because it reported
that targets were not scanned; `rootfs` mode positively detected existing
findings in the local cache. This is negative/detection evidence, not a clean
PASS, and does not establish that repository dependencies are clean. The
unavailable cloud credentials likewise do not establish a successful
credentialed plan.

Operational setup, local reproduction, triage, and the owner/rationale/ADR
waiver policy are documented in `config/security/README.md`.

## Validation evidence

| Check | Result |
|---|---|
| Dedicated security policy tests | `PASS`; 6 tests |
| Combined security and Terraform policy tests | `PASS`; 13 tests |
| Full Python policy suite | `PASS`; 96 tests |
| Gitleaks scan | `PASS`; Gitleaks 8.30.1 scanned 85 commits and approximately 1.23 MB with no leaks |
| Semgrep repository scan | `PASS`; Semgrep 1.187.0 ran 5 rules over 33 targets with 0 findings |
| zizmor workflow audit | `PASS`; zizmor 1.33.1 reported no findings (4 ignored, 3 suppressed) across the current two-workflow run |
| GitHub Actions semantic lint | `PASS`; actionlint 1.7.10 |
| `./gradlew check --no-daemon` | `PASS`; 106 actionable tasks (28 executed, 78 up-to-date) |
| Dependency vulnerability review | Local resolver populated 317 JARs. Trivy `fs` was rejected as not scanned; Trivy 0.70.0 `rootfs` detected existing local-cache findings. Negative/detection evidence only; no clean PASS or repository-clean claim. |
| Terraform credentialed plan/upload | Conditional on changed Terraform source under `infra/accounts` or `infra/modules`; cloud credentials unavailable in the initial environment, so no plan/upload PASS is claimed. |
| Required checks on `dev` | `NOT_RUN`; repository administration pending |
| `git diff --check` | `PASS` |

No result becomes `PASS` from documentation alone. Scanner findings must be
sanitized before being linked from Jira.

The service unit, ArchUnit, integration, API/event contract, and load/stress
categories are `NOT_RUN` because this ticket changes CI policy and scanner
configuration only. It changes no service behavior, architecture boundary,
database integration, executable contract, or runtime workload.

## Scope boundaries

- No image, SBOM, DAST, deployment, ECR publication, QA, or PROD change.
- No production credentials, personal data, or cross-account role use.
- No production-readiness, compliance, capacity, or penetration-test claim.
- Ignored `docs/` remains read-only and is not committed.

## Authoritative references

- `docs/01_Producto/Requisitos_Trazados/RTO_DEV.md` (`RTO-DEV-07`)
- `docs/09_DevOps/02_CI_CD_operacion_Jira.md`
- `docs/09_DevOps/03_Pipelines_migraciones_y_despiegues_por_ambiente.md`
- `docs/01_Producto/Requisitos_Trazados/RNF_SEC.md` (`RNF-SEC-11`,
  `RNF-SEC-18`)
- `docs/01_Producto/Requisitos_Trazados/RTO_SEC.md` (`RTO-SEC-01`,
  `RTO-SEC-04`)
- `docs/13_Pruebas/01_Plan_de_pruebas_y_calidad.md`

## Commit and pull request

- Security-gate remediation commit: `eeeabda809f412f733d9029529b27c51cd6f2aa7`
- Pull request: [#46](https://github.com/sumak-project/sumak-platform/pull/46) (target `dev`)
