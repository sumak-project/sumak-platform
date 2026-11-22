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
   - Before creating a new branch or starting a task, run `git fetch --prune origin` to refresh remote refs and remove deleted branches, then create the branch cleanly from `origin/dev` (avoid automatic `git pull` on branches with uncommitted changes).
- Synchronization rule (mandatory): before starting any new task or creating a new branch after a merge, sync the local dev branch by running:
  ```
  git checkout dev && git fetch --prune origin && git reset --hard origin/dev
  ```
  First verify with `git status` that there are no uncommitted local changes. Never auto-pull on a dirty working tree.
   - Always verify `git status` and `git diff` before committing; never blind `git add .` and never include `docs/` or secrets.

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
