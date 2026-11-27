# SCRUM-134 — Private S3 fallback evaluation

- **Record status:** `RECORDED`
- **Decision approval:** `PENDING`
- **Record date:** 2026-11-27
- **Jira:** SCRUM-134
- **Decision owner:** SUMAK platform architecture
- **Prerequisite:** `PENDING`
- **Fallback evaluation:** `NOT_RUN`
- **Infrastructure/AWS changes:** `NOT_RUN`
- **Scope:** Record the activation gate and evidence required before considering a signed reverse-proxy fallback for private asset delivery.

## Decision and status

The primary private-S3 + CloudFront Origin Access Control (OAC) path remains a conditional candidate. It must first receive authorized proof-of-concept (PoC) evidence. No OAC failure or denial is recorded, and no fallback ADR is approved; evaluating or approving a signed reverse-proxy fallback now would therefore be premature.

Bounded decision: retain OAC as the conditional primary candidate. Trigger fallback evaluation only after a recorded OAC PoC failure/denial with one of the permitted `BLOCKED_*` outcomes. External publication remains blocked until the prerequisite and subsequent decision are resolved. `RECORDED` here describes this decision record only; it is not `PASS`, approval, or runtime validation.

## Options and constraints

| Option | Current disposition |
| --- | --- |
| Private S3 + CloudFront OAC | Conditional primary candidate; authorized PoC evidence pending. |
| Signed reverse-proxy fallback | Not evaluated or approved; eligible for evaluation only after the activation gate below. |
| External publication | Blocked meanwhile. |

Any future path must preserve: private bucket; HTTPS; no public S3 website; no EC2 asset hosting; no custom IAM, IRSA, or cross-account assumptions; direct-origin access denied; presigned URLs not logged; and Cloudflare/API boundaries preserved.

## Activation gate and evidence

**Gate:** Record an authorized OAC PoC failure or denial and its permitted `BLOCKED_*` outcome before starting fallback evaluation. Until then, do not implement, approve, or publish via the fallback.

**Required OAC evidence before deciding:** authorization and scope; configuration/architecture; private-bucket and direct-origin-denial checks; CloudFront OAC delivery and HTTPS observations; Cloudflare/API boundary observations; relevant logs with presigned URLs excluded; exact result, timestamp, and evidence references. Record failure/denial explicitly as a permitted `BLOCKED_*` outcome if encountered.

**Required evidence for any later fallback evaluation:** bounded proposal/ADR; end-to-end HTTPS and authorization behavior; private origin and direct-origin denial; proof no prohibited IAM/IRSA/cross-account or EC2-hosting assumptions are introduced; Cloudflare/API boundary and logging/privacy checks; operational/security trade-offs; and authorized PoC result with reproducible evidence. Evaluation is not approval; approval requires the applicable decision authority.

## Acceptance results

| Acceptance result | Status |
| --- | --- |
| Conditional OAC primary and fallback activation gate recorded | `RECORDED` |
| Authorized OAC PoC prerequisite | `PENDING` |
| OAC PoC outcome / permitted `BLOCKED_*` trigger | `NOT_RUN` |
| Signed reverse-proxy fallback evaluation or approval | `NOT_RUN` |
| Infrastructure/AWS changes and runtime validation | `NOT_RUN` |
| External publication | Blocked |

## Quality gate and documentation impact

Markdown-only decision/evidence artifact; no executable behavior or infrastructure changed. All six mandatory quality-gate categories (unit, architecture, integration, contract, security, and load/stress) are not applicable to this change and `NOT_RUN`; no `PASS` is claimed. Infrastructure and runtime validation are also `NOT_RUN`. `git diff --check` is the applicable formatting check.

Documentation impact: this tracked evidence record documents the bounded decision and required future evidence. The authoritative `docs/` source remains untouched.

## Authoritative references

- `docs/00_Gobierno/02_Contradicciones_y_ADR.md`
- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`
- `docs/01_Producto/01_Idea_alcance_y_roles.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_DEV.md`
- `docs/05_Tecnologias/01_Inventario_y_decisiones.md`
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`
- `docs/06_AWS/02_Servicios_y_PoC.md`
- `docs/06_AWS/04_PoC_y_registro_de_decisiones_bloqueantes.md`
- `docs/08_Seguridad/01_Identidad_y_privacidad.md`
- `docs/08_Seguridad/04_Identidad_AD_Cloudflare_y_operacion_segura.md`
