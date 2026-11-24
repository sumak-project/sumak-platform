---
name: sumak-jira-git-flow
description: Run the SUMAK Jira and Git ticket lifecycle from bootstrap through a validated squash merge and Jira closure
---

## Roles and entry points

`@ops-git` owns the Jira/Git lifecycle through two operations. The primary agent supplies an epic when requested and passes the selected issue key between stages.

## `bootstrap-ticket`

1. Query Jira for an issue already assigned to the sole developer and in In Progress. Reuse it only when it belongs to the requested epic or no epic was requested; never start a second active ticket silently.
2. If none exists, select the next unresolved issue in Jira rank order from the requested epic. Without an epic, select the next issue from the prioritized backlog. Do not invent priority from issue keys or creation dates when Jira rank is available.
3. Assign an unassigned selected issue to the sole developer. Keep issues in Backlog or To Do branchless.
4. Transition the selected issue to In Progress before any branch is created.
5. Verify `git status` is clean. Never reset, switch, synchronize, or reuse a workspace containing unrelated changes. Use an isolated worktree when necessary to preserve existing work.
6. Fetch with pruning and establish the base from `origin/dev`. Synchronize a clean local `dev` with `git checkout dev && git fetch --prune origin && git reset --hard origin/dev` when operating in the primary worktree.
7. After the Jira transition, poll for the automation-created branch for at most 60 seconds. Verify that it is based on `origin/dev`; if it does not appear, create it from `origin/dev` as `<type>/SCRUM-<n>-<short-kebab-case>`, where type is `feat`, `fix`, `chore`, `refactor`, `test`, `docs`, or `ci`.
8. Check out the ticket branch and return the issue key, summary, epic, branch, base commit, workspace path, and acceptance criteria available from Jira.

## `close-ticket`

1. Confirm the current branch matches the issue key, targets one bounded Jira objective, and contains no unrelated or forbidden files.
2. Inspect `git status`, `git diff`, and the intended staged paths. Run `git diff --check` and every applicable repository-declared local check. A missing tool, failed test, or skipped mandatory gate is a blocker, not a pass.
3. Never use blind `git add .`. Stage only reviewed paths and inspect `git diff --cached` before committing.
4. Commit in English as `<type>(<scope>): <imperative summary> [SCRUM-<n>]` and push the ticket branch.
5. Open a small PR to `dev` with `gh`; use the same conventional title and include the issue key, bounded summary, and check evidence in the English body. Never target QA or PROD.
6. Ensure Jira reaches In Review after the PR opens. If repository automation does not transition it, transition it explicitly.
7. Wait for all required GitHub CI checks with `gh`. Do not merge while checks are pending, failing, cancelled, skipped when required, or absent when branch protection requires them.
8. Squash-merge the PR into `dev` only after required checks pass and the PR is mergeable. Delete the remote ticket branch.
9. Verify the merge, then synchronize a clean local `dev` from `origin/dev`. Never discard unrelated local work to synchronize it.
10. Add the PR URL and concise validation result to Jira, then transition the issue to Done. Verify the final Jira status and remote-branch deletion.

## Safety invariants

Never commit `docs/`, secrets, generated credentials, Terraform state, or unrelated formatting changes.
Never bypass branch protection, required checks, review requirements, or failed quality gates. Never claim PASS without command evidence.
