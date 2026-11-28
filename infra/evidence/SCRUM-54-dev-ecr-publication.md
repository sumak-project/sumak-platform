# SCRUM-54 — DEV ECR publication operation

## Implemented behavior

The manually dispatched `dev-ecr-publish.yml` workflow builds the approved
`config-svc` artifact, blocks publication on HIGH or CRITICAL image findings,
validates temporary credentials against DEV account `632080579751`, and
publishes only to `sumak/dev/config-svc` in `us-east-1`. It resolves the
destination ECR manifest digest and verifies recovery with an exact digest
pull. The workflow summary is credential-free and supplies the immutable
reference expected by the Helm chart.

The protected `dev` GitHub environment is the approval boundary. A dispatcher
must also enter `PUBLISH-DEV`. Repository administrators must configure the
three temporary credential secrets used by the workflow:
`SUMAK_DEV_AWS_ACCESS_KEY_ID`, `SUMAK_DEV_AWS_SECRET_ACCESS_KEY`, and
`SUMAK_DEV_AWS_SESSION_TOKEN`. They must be temporary values for the authorized
same-account writer and must be removed or renewed when the session expires.

## Boundaries and evidence status

- The workflow creates no IAM policy, OIDC trust, repository policy,
  replication, or cross-account path.
- `LabRole` publication is prohibited. Its separate read-path validation
  remains `NOT_RUN`.
- The published destination digest, account, region, repository, revision,
  approval, scan result, and exact pull result are captured by the workflow
  run. A run URL must be linked from Jira before runtime acceptance is `PASS`.
- Workflow implementation and local policy checks are not evidence of a new
  ECR publication. Until an authorized run completes, SCRUM-54 runtime
  publication is `NOT_RUN`.
- QA, PROD, EKS deployment, availability, capacity, and real-vote readiness
  are outside this operation.

SCRUM-142's prior same-principal push and exact-digest pull evidence remains in
[`SCRUM-142-ecr-digest-validation.md`](SCRUM-142-ecr-digest-validation.md).
