# SCRUM-53 security scanning evidence

## Implemented behavior

Pull requests targeting `dev` define separate checks for dependency
vulnerabilities, secrets in tracked history, and source/workflow security.
Scanner and action versions are pinned. The checks run with read-only
repository and pull-request permissions and do not consume AWS or production
credentials.

Operational setup, local reproduction, triage, and the owner/rationale/ADR
waiver policy are documented in `config/security/README.md`.

## Validation evidence

| Check | Result |
|---|---|
| Security policy tests | `PASS`; 5 tests |
| Full Python policy suite | `PASS`; 93 tests |
| Gitleaks clean scans | `PASS`; Gitleaks 8.30.1 scanned 84 commits plus 23.43 KB of modified/untracked ticket files and reported no leaks |
| Gitleaks generated negative fixture | `PASS`; a fictitious AWS-format identifier created and committed only in `/tmp/opencode` was rejected |
| Semgrep clean repository scan | `PASS`; Semgrep 1.187.0 ran 5 local rules over 33 applicable targets with 0 findings |
| Semgrep generated negative fixture | `PASS`; a Java process-execution fixture created only in `/tmp/opencode` was rejected |
| zizmor workflow audit | `PASS`; zizmor 1.33.1 reported no findings and 8 suppressed informational results |
| zizmor generated negative fixture | `PASS`; a write-all and unpinned-action workflow created only in `/tmp/opencode` was rejected |
| Workflow YAML parse | `PASS`; all workflows parsed with ruamel.yaml |
| GitHub Actions semantic lint | `PASS`; actionlint 1.7.10 |
| `./gradlew check --no-daemon` | `PASS`; 106 actionable tasks (32 executed, 74 up-to-date) |
| Dependency vulnerability review | `NOT_RUN`; requires the pull request comparison API |
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

- Commit: pending
- Pull request: pending (target `dev`)
