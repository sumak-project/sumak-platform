# DEV private PostgreSQL

This root declares plan-only private PostgreSQL capacity for the Identity and
Config service owners. It does not deploy QA/PROD resources or the isolated
ballot store.

## Safe workflow

1. Confirm the `sumak-dev` account mapping and run
   `aws sts get-caller-identity --profile sumak-dev`.
2. Initialize the locked same-account backend and provide reviewed VPC, private
   data subnet, and owner service security-group IDs.
3. Review `terraform plan`; verify no public endpoint, IAM resource, or resource
   outside the DEV account is proposed. Apply only with explicit authorization.
4. Through the private SSM administrative path, retrieve the AWS-managed master
   secret. In a `0700` directory on memory-backed storage, create four
   independent generated password files with mode `0600`. Install an exit trap
   that removes them. Never place a password in a command line, Terraform
   variable, state, shell history, source file, or persistent log.
5. Start `psql` with `sslmode=verify-full`. From that controlled session, load
   each password into a `psql` variable and execute `bootstrap.sql`. Send the
   matching values directly to the four Secrets Manager placeholders, verify
   the versions exist, then remove the temporary files before ending the SSM
   session. Do not print either the variables or secret responses.
6. As each migration login, execute `SET ROLE identity_owner` or
   `SET ROLE config_owner` before DDL and verify `current_role`. Migration
   tooling must perform this step for every migration connection; runtime
   logins are not members of either owner role.
7. Verify each runtime role can connect only to its database, cannot assume an
   owner role, and cannot create schemas or connect to the other owner's
   database. Run each owner's Flyway migration from scratch and upgrade checks
   before recording evidence.

Snapshot restore, isolation, Flyway, and outbox/invariant checks remain
`NOT_RUN` until authorized infrastructure exists. Never report them as passing
from this configuration alone.
