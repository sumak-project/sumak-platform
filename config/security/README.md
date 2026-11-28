# Security scanning

Pull requests targeting `dev` run three independent, fail-closed checks:

1. **Dependency vulnerability review** is incremental: it detects dependency-
   relevant Gradle inputs changed between reviewed base and head. If none
   changed, it reports an empty vulnerability delta. Otherwise it resolves
   every subproject's resolvable configurations into isolated
   `GRADLE_USER_HOME` and uses pinned Trivy 0.70.0 in `rootfs` mode to inspect
   cached JARs, failing closed on HIGH or CRITICAL findings. This avoids
   reliance on GitHub's dependency-graph API or repository settings.
2. **Secret scan** runs Gitleaks 8.30.1 over the complete Git history. The
   installer verifies the Linux x86-64 release checksum, and findings are
   redacted in logs.
3. **Source and workflow permission review** runs Semgrep 1.187.0 with the
   repository-owned rules in `semgrep.yml`, then zizmor 1.33.1 against GitHub
   Actions definitions. Neither tool requires production credentials.

## Local reproduction

Prerequisites are Python 3.12+, `curl`, `tar`, and standard GNU checksum tools.
Install tools outside the repository:

```bash
scripts/security/install-gitleaks.sh /tmp/opencode/sumak-security/bin
PATH="/tmp/opencode/sumak-security/bin:$PATH" \
  gitleaks git --redact --no-banner --exit-code 1 .

python3 -m venv /tmp/opencode/sumak-security/venv
/tmp/opencode/sumak-security/venv/bin/pip install semgrep==1.187.0 zizmor==1.33.1
/tmp/opencode/sumak-security/venv/bin/semgrep scan \
  --config config/security/semgrep.yml --metrics=off --error .
/tmp/opencode/sumak-security/venv/bin/zizmor \
  --min-severity medium --min-confidence medium --offline .
```

The dependency review check runs in CI as described above. An empty delta
applies only when no dependency-relevant Gradle inputs changed; it does not
assert that repository dependencies are clean.

Terraform formatting, backend-free initialization, validation, and
configuration scanning always run. Credentialed Terraform plans and uploads
run only when `*.tf` source under `infra/accounts` or `infra/modules` changes.
Those credentialed operations are intentionally conditional and are not
evidence of a successful plan when cloud credentials are unavailable.

## Triage and waivers

Do not paste a detected value into Jira, pull requests, logs, or evidence.
Revoke and rotate any real credential first, remove it from reachable history,
and then rerun the scan. Dependency and source findings must be fixed or
triaged by the code owner.

A waiver is exceptional and requires all of the following:

- a named owner and expiry or review date;
- written technical rationale and compensating controls;
- a reviewed ADR under `architecture/decisions/`;
- links from the pull request and Jira evidence.

There are no silent scanner exclusions. A documented waiver is
`WAIVED_WITH_ADR`, not `PASS`.

## Required GitHub configuration

Repository administrators must require these checks on `dev`:

- `Dependency vulnerability review`
- `Tracked source and history secret scan`
- `Source and workflow permission review`

Configuration outside the repository is reported as `NOT_RUN` or
`BLOCKED_PERMISSIONS` until verified. This scanning is DEV evidence only; it is
not a production-readiness, penetration-test, compliance, or capacity claim.
