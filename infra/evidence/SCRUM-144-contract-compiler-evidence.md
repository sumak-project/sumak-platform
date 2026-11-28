# SCRUM-144 official contract compiler evidence

## Scope and result

This change adds a read-only, fail-closed prerequisite guard for official
contract compiler execution and maps the package unit tests into PR validation.
It does not invent or install compiler versions, generate schemas, certify the
162 candidate operations, or report official compilation as passing.

**Official compiler result: `BLOCKED_CONTRACT`.**

The authoritative contract archive and `validacion/COMPILADORES.md` are absent.
The tracked catalog reports 162 pending operations, zero generated contracts,
and zero executable schema inputs. Compiler execution is therefore `NOT_RUN`.

## Validation context

- Base commit: `6a8021ce84df097c59ebe72cda04430597410a6e`
- Branch: `ci/SCRUM-144-contract-compiler-evidence`
- Executed at: `2026-11-28T14:43:39Z`
- Environment: local Linux workspace
- Dataset: tracked candidate matrix, pending executable catalog, and synthetic
  temporary manifests/schemas used only by guard tests
- AWS / database / runtime: not used

## Commands and observed results

| Command | Result |
|---|---|
| `python3 -m unittest tests.test_official_contract_compiler_gate -v` | PASS — 5 guard/policy tests |
| `python3 -m unittest discover -s tests -v` | PASS — 142 repository tests |
| `./gradlew check --no-daemon` | PASS — build successful; 106 actionable tasks, 28 executed and 78 up-to-date |
| Seven deterministic contract commands from `contracts/executable/README.md`, followed by `python3 -m unittest discover -s tests -v` from `contracts/executable/` | Commands executed; deterministic structure/policy checks passed, while catalog/traceability/compatibility outputs truthfully remained `PENDING` with 162 pending and zero generated |
| `GITHUB_SHA=$(git rev-parse HEAD) python3 scripts/ci/check_official_contract_compilers.py --root . --manifest contracts/executable/validacion/compiler-manifest.json --evidence /tmp/opencode/SCRUM-144-contract-compiler-evidence.json` | `BLOCKED_CONTRACT`, exit 1; manifest missing, zero executable schemas, `compilerExecution: NOT_RUN` |
| YAML parse of `.github/workflows/pr-validation.yml` | PASS |
| `git diff --check` | PASS |

The guard tests use isolated temporary roots. They verify missing schemas or
manifests, malformed manifests, and unpinned versions block without modifying
inputs. A synthetically complete prerequisite set yields only
`PREREQUISITES_VALID` and `compilerExecution: NOT_RUN`, never `PASS`.

## Quality-gate classification

| Gate | Status | Evidence / limitation |
|---|---|---|
| Unit | PASS | Focused 5-test guard suite and full 142-test repository suite passed. |
| Architecture | PASS | Gradle architecture-boundary checks completed successfully. |
| Integration | NOT_RUN | No database, broker, migration, or service adapter was exercised. |
| Contract | BLOCKED_CONTRACT | Official archive, version pins, commands, and executable schemas are absent; official compilers were not run. |
| Security | NOT_RUN | PR security scanning has not yet executed for this branch. |
| Load/Stress | NOT_RUN | No deployed workload or load target is in scope. |

## Unblocking requirements

1. Recover the authoritative
   `SUMAK_MVP_v2_1_Contratos_Ejecutables` archive and review its
   `validacion/COMPILADORES.md`.
2. Version reviewed exact compiler versions and commands; do not infer them.
3. Resolve approved operation mappings into real executable schemas.
4. Execute each official compiler against those schemas and retain
   commit-bound command, version, exit status, and output evidence.
5. Keep generated outputs and compatibility/Protobuf baselines under explicit
   versioning review; never refresh them automatically.

No ignored `docs/` content, generated contract output, or baseline was edited.
