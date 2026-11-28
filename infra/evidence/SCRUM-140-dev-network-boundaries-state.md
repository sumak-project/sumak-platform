# SCRUM-140 — DEV network-boundaries state evidence

## Scope and account verification

This record covers only the approved `sumak-dev` network-boundaries Terraform
root in `us-east-1`. STS account verification matched the `sumak-dev` account
map entry (account suffix `9751`). No role-session or user suffix is recorded.

The Terraform backend was the configured remote S3 bucket and key for this
root. The state object was verified to exist, with versioning enabled and
server-side AES256 encryption. Plans and state material remained under
`/tmp/opencode/` and were not added to Git.

## Plan, apply, and state verification

- Reviewed plan: **11 add, 0 change, 0 destroy** — five security groups and
  six rules referencing security groups.
- Apply result: **11 add, 0 change, 0 destroy**.
- Post-apply detailed-exitcode plan: **no changes**.
- All four expected output groups were verified.
- No ALB, QA/PROD, or unrelated resources were in scope or changed.

These results describe the recorded Terraform operations only; they do not
assert broader environment readiness or production suitability.

## Recovery and authoritative references

- Teardown and recovery procedures: `infra/evidence/SCRUM-39-dev-teardown-recovery-runbook.md`.
- Network-boundary implementation: `infra/accounts/sumak-dev/us-east-1/dev/network-boundaries/`.
- State backend guidance: `infra/accounts/sumak-dev/us-east-1/dev/state-backend/README.md`.
- Network security-group module: `infra/modules/network-security-groups/`.
- Account/environment ownership map: `infra/accounts-map.yaml`.
- Authoritative governance: `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`.
- Network requirements: `docs/01_Producto/Requisitos_Trazados/RTO_NET.md`.
- Infrastructure policy requirements: `docs/01_Producto/Requisitos_Trazados/RTO_IAC.md`.
- Pipeline and apply controls: `docs/09_DevOps/02_CI_CD_operacion_Jira.md` and
  `docs/09_DevOps/03_Pipelines_migraciones_y_despiegues_por_ambiente.md`.

Ignored `docs/` remains read-only and was not modified.
