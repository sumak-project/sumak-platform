# ADR-0002: Defer the Conditional ECS/Fargate Fallback

- **Record status:** `RECORDED`
- **Decision approval:** `PENDING`
- **Decision date:** 2026-11-27
- **Jira:** SCRUM-135
- **Decision owner:** SUMAK platform architecture
- **EKS PoC:** `PENDING`
- **Fallback activation gate:** Not triggered
- **ECS/Fargate evaluation:** `NOT_RUN`
- **Infrastructure/AWS changes:** `NOT_RUN`

## Context

Amazon EKS remains the conditional orchestration target for the DEV environment.
The required AWS-02 proof of concept has not run, so EKS is neither proven nor
failed. Existing evidence is limited to role visibility and policy simulation;
it does not demonstrate cluster creation or workload operation.

The managed node group planned by SCRUM-40 is blocked by the missing EKS control
plane in SCRUM-46. That dependency is not an EKS failure and does not activate a
fallback. Learner Lab permissions, quotas, operational fit, and cost also remain
unmeasured at runtime.

## Decision

Keep EKS as the target direction and defer the ECS/Fargate fallback decision.
Evaluate ECS/Fargate only after an authorized EKS PoC records a failure or denial
using an applicable `BLOCKED_*` status. Until that activation gate is met:

- do not implement, provision, or approve ECS/Fargate;
- do not build a duplicate orchestration platform;
- do not interpret `PENDING` or `NOT_RUN` as an EKS failure; and
- continue prerequisite work without claiming EKS runtime validation.

`RECORDED` describes this ADR only. It is not `PASS`, approval, runtime
validation, or evidence that either platform is feasible in Learner Lab.

## Conditional options

| Option | Current disposition |
| --- | --- |
| Amazon EKS | Conditional target; authorized AWS-02 runtime PoC is `PENDING`. |
| Amazon ECS/Fargate | Conditional fallback; activation gate not triggered and evaluation `NOT_RUN`. |
| Parallel EKS and ECS platforms | Rejected; duplicates infrastructure and operational scope without evidence. |

If the gate is triggered, the fallback evaluation must compare at least:

- Learner Lab service access, quotas, required API actions, and `iam:PassRole`;
- use of pre-provisioned roles without custom IAM, IRSA, or `AssumeRole`;
- private networking, load-balancer integration, secrets, and image delivery;
- workload isolation, health, rollout, rollback, logs, metrics, and teardown;
- Terraform ownership, state boundaries, migration effort, and operational load;
- measured capacity and cost using sanitized synthetic workloads.

Evaluation would not itself approve ECS/Fargate. A subsequent ADR and applicable
decision authority would be required before implementation.

## Activation gate and evidence

The fallback evaluation may start only when all of these conditions are met:

1. The EKS PoC has explicit authorization, a reviewed plan, and a cleanup plan.
2. The PoC records its date, account alias, region, role, IaC revision, actions,
   observed quotas, result, and sanitized errors or captures.
3. Cluster creation, node integration, or required role passing fails or is
   denied for a reason that cannot be resolved within the approved Learner Lab
   boundary.
4. The result uses a precise status such as `BLOCKED_AWS_PERMISSION`,
   `BLOCKED_QUOTA`, `BLOCKED_SECURITY`, or `BLOCKED_EXTERNAL_DEPENDENCY`.
5. The decision owner confirms that the evidence activates fallback evaluation.

The current state does not satisfy these conditions. SCRUM-30 provides bounded
policy-level evidence only, while SCRUM-40 reports a missing control-plane
dependency. AWS-02 and the ECS/Fargate evaluation therefore remain `PENDING` and
`NOT_RUN`, respectively.

## Boundaries and consequences

- This ADR applies to DEV only and creates no QA or production direction.
- No ECS service, task, cluster, capacity provider, load balancer, image, IAM
  role, network resource, or Terraform configuration is authorized or created.
- No AWS mutation, runtime test, quota measurement, or cost measurement occurred.
- No custom IAM, IRSA, `AssumeRole`, or cross-account state is permitted.
- EKS must not be described as proven, failed, available, secure, performant, or
  cost-validated without measured evidence.
- The ignored `docs/` tree remains unchanged and authoritative.

## Validation record

| Evidence | Status | Notes |
| --- | --- | --- |
| Conditional target and activation gate | `RECORDED` | This ADR records the boundary only. |
| Authorized EKS AWS-02 PoC | `PENDING` | No runtime creation evidence exists. |
| EKS failure or permitted blocker trigger | `NOT_RUN` | Missing prerequisites are not platform failure. |
| ECS/Fargate feasibility and comparative evaluation | `NOT_RUN` | Activation gate was not triggered. |
| ECS/Fargate approval or implementation | `NOT_RUN` | No fallback was approved. |
| Infrastructure and AWS runtime validation | `NOT_RUN` | No AWS mutation was authorized or performed. |

This is a Markdown-only architecture decision. Unit, architecture, integration,
contract, security, and load/stress test categories are not applicable and are
`NOT_RUN`; no `PASS` is claimed. `git diff --check` and content review against
the cited sources are the applicable static validation.

## Documentation impact

This tracked ADR is the documentation deliverable. It changes no contract,
setup, runtime, or operational behavior, so there is no other documentation
impact. Authoritative `docs/` sources were not modified.

## Authoritative references

- `docs/00_Gobierno/02_Contradicciones_y_ADR.md`
- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_IAC.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_SEC.md`
- `docs/05_Tecnologias/01_Inventario_y_decisiones.md`
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`
- `docs/06_AWS/02_Servicios_y_PoC.md`
- `docs/06_AWS/03_Mapa_de_recursos_y_dependencias_por_cuenta.md`
- `docs/06_AWS/04_PoC_y_registro_de_decisiones_bloqueantes.md`
- `docs/09_DevOps/03_Pipelines_migraciones_y_despiegues_por_ambiente.md`
- `docs/13_Pruebas/01_Plan_de_pruebas_y_calidad.md`
- `infra/evidence/SCRUM-30-learner-lab-validation.md`
- `infra/evidence/SCRUM-40-dev-eks-managed-node-group.md`
