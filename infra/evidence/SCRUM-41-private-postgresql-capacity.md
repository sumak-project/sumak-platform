# SCRUM-41 — private PostgreSQL capacity evidence

- Scope: reusable private PostgreSQL module and DEV-only Identity/Config root.
- Implementation status: `IMPLEMENTED_PLAN_ONLY`.
- Terraform plan/apply and AWS-05/P06 runtime PoC: `NOT_RUN`.
- Database bootstrap, isolation, Flyway, snapshot restore, grants, invariants,
  and outbox checks: `NOT_RUN`.

## Implemented boundaries

- One encrypted `gp2` PostgreSQL instance, limited to `db.t3.medium` and 100 GiB.
- Private data subnet group, no public endpoint, and ingress only from the
  supplied Identity and Config service security groups.
- TLS is forced; Enhanced Monitoring and Multi-AZ are not enabled.
- The administrator password is managed by RDS. Separate runtime and migration
  secret placeholders and a reviewed bootstrap procedure are provided.
- Deletion protection and a final snapshot are required.
- State uses the encrypted same-account S3 backend with native lock files.

## Validation status

- `terraform fmt -recursive infra`: `PASS`.
- `terraform init -backend=false && terraform validate` in the DEV PostgreSQL
  root: `PASS` with `hashicorp/aws` 6.74.0.
- `python3 -m unittest tests.test_dev_postgresql_capacity_boundaries -v`:
  `PASS` (5 tests).
- `python3 -m unittest discover -s tests -v`: `PASS` (51 tests).
- `git diff --check`: `PASS`.

No static check is runtime, availability, capacity, restore, or security PoC
evidence. Before any plan or apply, verify temporary `sumak-dev` credentials
and exact account `632080579751`; stop on permissions, quota, or identity
mismatch.

## Authoritative references

- `docs/00_Gobierno/04_Fuentes_verificadas_y_omisiones.md`.
- `docs/06_AWS/01_Cuentas_red_y_capacidad.md`.
- `docs/06_AWS/03_Mapa_de_recursos_y_dependencias_por_cuenta.md`.
- `docs/10_Datos/00_Indice_y_arquitectura.md`.
- `docs/10_Datos/05_Persistencia_fisica_por_region_cuenta_y_AZ.md`.
- `docs/01_Producto/Requisitos_Trazados/RTO_IAC.md`.
- `docs/01_Producto/Requisitos_Trazados/RNF_SEC.md`.
- `docs/01_Producto/Requisitos_Trazados/RTO_SEC.md`.
- `docs/13_Pruebas/02_Pruebas_de_bases_y_restauracion_por_propietario.md`.
