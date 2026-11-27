# SUMAK repository guidance

## Workflow rules (Jira + Git) — mandatory

All technical artifacts (tickets, branches, commits, PRs, code) MUST be in English.

1. Jira + Git automation flow:
   - When an issue is created in Jira without an assignee, auto-assign it to me (the sole developer).
   - While a ticket is in Backlog / To Do, NO Git branch is created.
   - Only when the ticket moves to In Progress, create the working branch from `origin/dev`.
   - When a Pull Request targeting `dev` is opened with the issue key in its title/body, the Jira issue must move automatically to In Review.
   - When the PR is merged into `dev`, the Jira issue must move to Done and the remote branch must be deleted automatically.

2. Naming conventions (100% English):
   - Branches: `<type>/<ISSUE-KEY>-<short-kebab-case>` (types: feat, fix, chore, refactor, test, docs, ci). Example: `feat/SUMAK-12-identity-domain`.
   - Commits (Conventional Commits): `<type>(<scope>): <imperative summary in English> [<ISSUE-KEY>]`. Example: `feat(identity): add user aggregate [SUMAK-12]`.
   - Pull Requests: same format as the main commit, always targeting `dev` at this stage.

3. Scope and safety best practices in Git:
   - Forbidden: giant commits/PRs with thousands of lines or mixed functionalities. Each branch, commit and PR must resolve a single, bounded objective.
   - Enrich tickets incrementally when they are selected for implementation; do not delay delivery to rewrite the whole backlog.
   - Before moving a selected ticket to In Progress, complete its Jira description in English with: objective and bounded scope, authoritative `docs/` references, concrete deliverables, verifiable acceptance criteria, exclusions or constraints, and expected validation evidence. Keep this documentation concise and specific to the selected task.
   - If the existing summary is generic, use the authoritative documentation and epic context to clarify the ticket without expanding it beyond one bounded objective. Never invent requirements; record unresolved ambiguity as a blocker.
   - Complete each implemented ticket with proportionate documentation as an explicit deliverable. Update tracked, code-adjacent documentation when behavior, contracts, setup, or operations change; otherwise record `No documentation impact` with the reason in the PR and Jira evidence. Never edit the ignored `docs/` source of truth for this purpose.
   - Before creating a new branch or starting a task, run `git fetch --prune origin` to refresh remote refs and remove deleted branches, then create the branch cleanly from `origin/dev` (avoid automatic `git pull` on branches with uncommitted changes).
- Synchronization rule (mandatory): before starting any new task or creating a new branch after a merge, sync the local dev branch by running:
  ```
  git checkout dev && git fetch --prune origin && git reset --hard origin/dev
  ```
  First verify with `git status` that there are no uncommitted local changes. Never auto-pull on a dirty working tree.
   - Always verify `git status` and `git diff` before committing; never blind `git add .` and never include `docs/` or secrets.

## Subagent Delegation Policy

Classify every user turn by its requested work before taking action:

- **Git, Jira, and pull request operations:** delegate ticket selection, assignment, transitions, branch preparation, commits, pushes, pull requests, CI waiting, merges, branch cleanup, and Jira closure to `@ops-git`, which MUST follow `/sumak-jira-git-flow`. This delegation replaces direct execution by the primary agent for those lifecycle operations; the primary agent remains responsible for orchestration and final verification.
- **Architecture and implementation work:** for architecture, Java code, Terraform, AWS infrastructure, or quality tasks, the active agent acts as architect and coordinator. It MUST delegate the applicable work below automatically before editing:
  - Delegate every read or analysis of `docs/`, and every extensive repository exploration, to `@docs-researcher`. Consume only its compact summary of authoritative contracts, constraints, and acceptance criteria.
  - Delegate every creation or update of Unit, ArchUnit, Integration, Contract, or Security tests to `@test-builder`, which MUST follow `/sumak-quality-gate`.
  - Delegate runbook and operational documentation drafting, Terraform or YAML format validation, diff review, and PR readiness to `@ops-git`.

The primary agent reserves its context and tools for architecture decisions, core domain and contract design, critical AWS MCP calls, integration of delegated results, and final review. Delegation does not transfer responsibility for the final result, and subagents must remain within their configured read, edit, and command permissions.

## Autopilot by Ticket

When the user asks `ejecuta el siguiente ticket` or `continúa con la épica X`, the primary agent MUST orchestrate the following sequence automatically. Do not ask for confirmation between stages unless a safety blocker, missing authorization, failed required check, or ambiguous epic prevents progress.

1. Invoke `@ops-git` with `bootstrap-ticket` to find an existing In Progress issue or identify the next issue from the requested epic or prioritized backlog. For a To Do issue, return its epic context and current fields without transitioning it or creating a branch yet.
2. Invoke `@docs-researcher` to read `docs/` and return the authoritative scope, constraints, deliverables, acceptance criteria, documentation references, and expected validation evidence for that ticket.
3. Invoke `@ops-git` to update the selected Jira issue in English with the research summary, assign it when unassigned, transition it to In Progress, and prepare a clean workspace on a correctly named branch from `origin/dev`.
4. The primary agent implements the bounded core change, including application code, Terraform, or policy files as applicable, while integrating the research summary.
5. Invoke `@test-builder` for applicable Unit, ArchUnit, Integration, Contract, or Security tests and mandatory quality-gate evidence. If no test category applies, record the reason explicitly instead of inventing a passing result.
6. Invoke `@ops-git` with `close-ticket` to validate the diff and local checks, create the English conventional commit, push, open the PR to `dev`, wait for required CI, squash-merge, delete the remote branch, synchronize local `dev`, add the PR link and validation evidence to Jira, and transition the issue to Done.

Each stage must receive the issue key and the relevant output of the previous stage. Stop the sequence on a dirty-worktree conflict, failed mandatory check, CI failure, merge conflict, expired credentials, or Jira/GitHub authorization failure; report the blocker without bypassing safeguards.

## Git and environments

- Repository remote: `https://github.com/sumak-project/sumak-platform.git` (org `sumak-project`, repo `sumak-platform`). Default branch is `dev`. Authenticated via the GitHub MCP server token configured in `~/.config/opencode/opencode.json` (`GITHUB_PAT`).
- `dev` is the only working branch and active environment for now. Do not create, configure, merge into, or deploy `qa`/`prod`; those remain reserved until the required tests and validations exist.
- When the user says "sube a git" / "upload to git", push the current working tree to `origin dev` of `sumak-project/sumak-platform` (commit pending changes first if needed, respecting `.gitignore` which excludes `docs/`). Use the token above if git credentials are missing.">

- Do not run `git init`, add remotes, create the first commit, or perform the first push. The remote already exists with `dev` as its main branch; the user owns repository initialization and first publication.
- The repository is now only an initial monorepo skeleton. There is no Gradle Wrapper or implemented application yet; do not report builds, deployments, tests, capacity, security, or AWS resources as implemented or passing.
- Commands in `docs/09_DevOps/01_Monorepo_Gradle.md` describe the target monorepo and remain non-runnable until the corresponding toolchains and modules are implemented.
- `docs/` is intentionally ignored by Git and must remain available locally as a read-only source of truth. Do not edit, move, delete, or force-add it.
- Machine-readable contracts are stored only in `docs/11_Contratos/SUMAK_MVP_v2_1_Contratos_Ejecutables.{zip,tar.gz}`. The `ejecutables/` links in `07_Contratos_implementables.md` do not resolve in the working tree.

## Authority and navigation

- Read `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md` before older v2.0 governance notes. In particular, requirements v2.5 were received; do not repeat the obsolete “missing F02” claim.
- Resolve conflicts in this order: latest explicit MVP direction; undisplaced v2.5 requirements; Learner Lab v1.2 limits; original DB/API designs; then the v2.0 redesign. See `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`.
- Use `docs/01_Producto/Requisitos_Trazados/` for individual RF/RNF/RTO text and status. Preserve both occurrences of `RF-NEWS-05` and `RF-NEWS-06`; they are intentional duplicate identifiers with different wording.
- Service boundaries come from `docs/03_Microservicios/01_Catalogo.md`; persistence ownership and fields come from `docs/10_Datos/<service>.md`; cross-service protocols come from `docs/11_Contratos/`.
- Treat the 162-route API mapping as candidate/partial, not certified equivalence. `03_Trazabilidad_API_original.md` is historical; the current limitation is recorded in `06_Verificacion_API_v2_5_1_y_alcance_GraphQL.md`.

## Non-obvious constraints

- Preserve evidence language: `propuesto`, `pendiente`, `NOT_RUN`, or a documented blocker is not `PASS`, approval, or implementation. A document or screenshot alone is not runtime evidence.
- Do not introduce business REST merely to provide Swagger. The target split is GraphQL for clients, gRPC internally, Kafka for facts/replay, RabbitMQ for work, WSS for notifications, and HTTP only for authorized webhooks/technical interfaces.
- The proposed 22 services own 19 independent PostgreSQL databases and 3 DynamoDB tables. No cross-owner SQL/FKs/migrations or shared JPA/domain DTOs; integrations use versioned contracts. Keep voter eligibility, anonymous ballot, and tally stores/services separated.
- Never claim real-vote readiness, >100k capacity, legal/fiscal compliance, AWS availability, WCAG compliance, RPO/RTO, or use of real personal data without the approvals and measured evidence identified in governance and QA docs.

## Contract package verification

- Extract archives to a temporary directory (prefer `/tmp/opencode`), not over `docs/`. Inside the extracted package, Python 3.10+ and Node 20+ are expected.
- Fast local checks documented by the package:

  ```bash
  python3 tools/generar.py
  python3 tools/integraciones.py
  python3 tools/trazabilidad.py
  node tools/validar.cjs
  python3 -m unittest discover -s tests -v
  python3 tools/revisar_estructura.py
  ```

- Official compiler checks additionally require network-installed dependencies; follow the archived `README.md` and `validacion/COMPILADORES.md`. Missing GraphQL/AsyncAPI/Protobuf/OpenAPI tooling is a failure/pending gate, never an implicit pass.
- Contract schemas and generated outputs are regenerated deterministically; do not hand-edit generated files. Never refresh `catalogo/schemas-baseline.json` or Protobuf tag baselines automatically. Existing fields/tags require explicit versioning review; removed Protobuf fields reserve both name and number.
