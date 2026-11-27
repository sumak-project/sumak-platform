# SCRUM-35 — ACM, DNS, and TLS proof of concept

**Status:** BLOCKED_EXTERNAL_DEPENDENCY

**Infrastructure change:** NOT_RUN

**Terraform plan/apply:** NOT_RUN

## Bounded scope

Assess whether the DEV account in `us-east-1` has the externally authorized
DNS/certificate prerequisites for an ACM and TLS proof of concept. This record
captures read-only discovery only; it does not provision DNS, certificates,
load balancers, or application endpoints.

## Authoritative references

The applicable Learner Lab and AWS account/environment constraints, security
boundaries, and infrastructure authorization guidance are defined by the
authoritative materials in `docs/06_AWS/`, `docs/08_Seguridad/`, and
`docs/00_Gobierno/`. The relevant DNS/domain ownership and authorization
requirements must be satisfied before a public endpoint can be configured.
These references remain the source of truth and are not reproduced or amended
here.

## Discovery results

Observed on 2026-11-27 at approximately 17:03 UTC using AWS API with profile
`sumak-dev`, region `us-east-1`.

| Check | Result | Evidence |
|---|---|---|
| STS identity | PASS | Valid temporary assumed-role session; account suffix `****9751` matches `sumak-dev` in `infra/accounts-map.yaml`. Full account ID and principal ARN intentionally omitted. |
| ACM certificates | BLOCKED_EXTERNAL_DEPENDENCY | `list-certificates` returned 0 certificates. |
| Route 53 hosted zones | BLOCKED_EXTERNAL_DEPENDENCY | `list-hosted-zones` returned 0 hosted zones. |
| ELBv2 load balancers | BLOCKED_EXTERNAL_DEPENDENCY | `describe-load-balancers` returned 0 load balancers. |
| DNS/TLS/HTTPS/origin protection/WSS/health | NOT_RUN | No authorized domain, certificate, or endpoint exists to validate these behaviors. |
| Writes or infrastructure changes | NOT_RUN | No resources were created; no Terraform plan or apply was run. |
| Cost and cleanup | NOT_RUN | No billable resources were created; no cleanup was required. |

Sanitized read-only commands used:

```bash
aws sts get-caller-identity --profile sumak-dev --region us-east-1
aws acm list-certificates --profile sumak-dev --region us-east-1
aws route53 list-hosted-zones --profile sumak-dev --region us-east-1
aws elbv2 describe-load-balancers --profile sumak-dev --region us-east-1
```

No request IDs, full account IDs, complete ARNs, credentials, or secrets are
included.

## Blocker and constraints

The global outcome is **BLOCKED_EXTERNAL_DEPENDENCY**. Learner Lab does not
permit registering a new domain for this purpose. A domain name, hosted zone,
or certificate must not be invented or treated as authorized. DNS ownership
and a usable certificate are prerequisites for meaningful TLS/HTTPS and
origin-protection validation; without them, WSS and health checks are also
NOT_RUN.

No writes were performed. There was no Terraform plan/apply, resource
provisioning, cost incurred, or cleanup activity. This evidence does not claim
TLS, HTTPS, DNS, origin protection, WSS, or health behavior works.

## Acceptance criteria and outcome

| Criterion | Result |
|---|---|
| Confirm the selected DEV identity and region | PASS — temporary STS identity validated; account suffix matches the account map. |
| Discover existing certificate, hosted zone, and load balancer prerequisites | PASS — the read-only API queries returned zero for each. |
| Avoid unauthorized domain registration and all infrastructure writes | PASS — no registration or writes were attempted. |
| Demonstrate DNS/TLS/HTTPS, origin protection, WSS, and health | NOT_RUN — blocked by missing authorized domain and prerequisites. |
| Complete an end-to-end ACM/DNS/TLS proof of concept | BLOCKED_EXTERNAL_DEPENDENCY — requires an authorized institutional domain/hosted zone and certificate path. |

## Action required

Obtain an institutional domain and hosted zone explicitly authorized for DEV,
including confirmation of DNS control and certificate issuance/validation
ownership. Then schedule a separate, explicitly scoped execution with reviewed
costs and authorization. Only that follow-up may plan/provision the required
resources and record runtime validation evidence. This ticket does not grant
deployment authorization.

## Documentation impact

Adds tracked operational evidence of read-only discovery, the external
dependency, and the required follow-up. No `docs/` source-of-truth files are
changed.
