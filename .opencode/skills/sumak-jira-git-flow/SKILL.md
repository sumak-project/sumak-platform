---
name: sumak-jira-git-flow
description: Enforce the SUMAK Jira lifecycle, dev-based branch naming, English commits, and small pull requests
---

## Mandatory workflow

1. Keep the issue in To Do without a branch. Assign unassigned work to the sole developer.
2. Move the issue to In Progress before creating a branch.
3. Verify `git status` is clean. Never reset, switch, or synchronize a dirty tree.
4. Synchronize with `git checkout dev && git fetch --prune origin && git reset --hard origin/dev` only after the clean-tree check.
5. Create the branch from `origin/dev` as `<type>/SCRUM-<n>-<short-kebab-case>`, where type is `feat`, `fix`, `chore`, `refactor`, `test`, `docs`, or `ci`.
6. Keep each branch, commit, and PR limited to one Jira objective. Never use blind `git add .`; inspect `git status`, `git diff`, and staged changes.
7. Commit in English as `<type>(<scope>): <imperative summary> [SCRUM-<n>]`.
8. Open a small PR to `dev` with the issue key in the English title and body. Never target QA or PROD branches at this stage.
9. The PR must move the issue to In Review. After merge to `dev`, ensure Jira reaches Done and the remote branch is deleted.
10. Synchronize local `dev` from `origin/dev` after the merge, but never discard unrelated local work.

Never commit `docs/`, secrets, generated credentials, Terraform state, or unrelated formatting changes.
