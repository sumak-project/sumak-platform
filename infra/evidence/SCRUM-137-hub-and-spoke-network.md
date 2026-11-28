# SCRUM-137 — Hub-and-spoke network evaluation evidence

## Scope

This record covers the documentation-only comparison of an
instructor-proposed hub-and-spoke topology with SUMAK's authoritative isolated
per-account VPC baseline. The resulting decision is recorded in
`architecture/decisions/ADR-0004-defer-hub-and-spoke-network.md`.

No Terraform or AWS resource was created, changed, queried, or deleted. No
runtime, permission, quota, capacity, cost, or compatibility test was
authorized or performed.

## Evidence

| Check | Status | Result |
| --- | --- | --- |
| Authoritative topology and source precedence review | `REVIEWED` | Ten isolated accounts, per-account VPC/state/ECR, and no implied inter-account trust remain the baseline. |
| TGW, VPC peering, VPN/Direct Connect, and cross-account IAM assessment | `RECORDED` | Each mechanism is explicitly excluded, prohibited, or unproven pending authorization and evidence. |
| ADR decision and activation gates | `RECORDED` | Adoption is deferred; AWS-14 and a subsequent approval are required. |
| Decision approval | `PENDING` | Documentation does not approve a topology change. |
| AWS-14 inter-account network PoC | `PENDING` | No authorized plan or execution evidence exists. |
| AWS/runtime validation | `NOT_RUN` | No AWS mutation occurred. |

`RECORDED` and `REVIEWED` describe static documentation work only. They do not
mean `PASS`, runtime feasibility, approval, or implementation.

## Exclusions and blockers

- Transit Gateway, general VPC peering, VPN, Direct Connect, AWS Organizations,
  SCP, custom IAM, IRSA, and cross-account `sts:AssumeRole` were not authorized.
- No cross-account state, ECR, secret centralization, shared-services
  dependency, QA/production direction, or real data is in scope.
- Missing permissions or quotas in a future PoC must be recorded precisely as
  `BLOCKED_AWS_PERMISSION`, `BLOCKED_QUOTA`, `BLOCKED_SECURITY`, or
  `BLOCKED_EXTERNAL_DEPENDENCY`; they must not be worked around.

## Validation and documentation impact

Applicable validation is source-content review plus `git diff --check`. Unit,
architecture, integration, contract, security, and load/stress tests are not
applicable to this Markdown-only change and remain `NOT_RUN`; no `PASS` is
claimed.

The ADR and this record are the complete tracked documentation impact. They
change no contract, setup, runtime, or operational behavior. Authoritative
`docs/` sources remain read-only and unchanged.

## Authoritative references

- `docs/00_Gobierno/02_Contradicciones_y_ADR.md`
- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_HA.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_IAC.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_NET.md`
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`
- `docs/06_AWS/03_Mapa_de_recursos_y_dependencias_por_cuenta.md`
- `docs/06_AWS/04_PoC_y_registro_de_decisiones_bloqueantes.md`
- `docs/08_Seguridad/02_Continuidad_y_backups.md`
