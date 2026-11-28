# SCRUM-51 architecture boundary checks

**Record status:** IMPLEMENTED; validation commands below were independently rerun.

## Behavior and gate

The shared Java convention plugin adds `architectureBoundaryCheck`, which rejects Gradle project dependencies in `api`, `implementation`, `compileOnly`, and `runtimeOnly` configurations. Every Java module using the convention plugin wires this task into its `check` task. The identity, Config, and API gateway architecture tests enforce service/package isolation, hexagonal boundaries, and acyclic package slices.

Run the aggregate gate from the repository root. Independently rerun result:

```bash
./gradlew check --no-daemon
```

**BUILD SUCCESSFUL** in 15 seconds; 106 tasks (28 executed, 78 up-to-date).

```bash
python3 -m unittest discover -s tests -v
```

**86 tests passed** (`OK`).

## Negative check

The following command completed with **BUILD FAILED as expected** in 11 seconds and emitted the injected implementation project dependency:

```bash
./gradlew :services:identity-svc:architectureBoundaryCheck --no-daemon \
  -ParchitectureBoundaryCheck.injectProjectDependency=:services:config-svc
```

Observed diagnostic: `:services:identity-svc:implementation -> project(:services:config-svc) [negative test]`. This is an opt-in synthetic violation proving the task rejects a project-dependency violation; it is not evidence that a real cross-service dependency was introduced.

**Environment:** Gradle 8.14.3; OpenJDK 21.0.13.1; Linux amd64.

## Scope and limitations

No contract-schema validation, Testcontainers/Flyway, Docker/SBOM/ECR, Terraform/Kubernetes, promotion, runtime/load/security validation, or business REST behavior is included or claimed. No claim is made here about checks on modules not represented by the reported targeted tests beyond the shared convention-plugin wiring and aggregate command result.

The ignored `docs/` source of truth was not edited. No application runtime or deployment validation is represented by these checks.

## Authoritative references

- `docs/09_DevOps/03_Pipelines_migraciones_y_despiegues_por_ambiente.md`
- `docs/13_Pruebas/01_Plan_de_pruebas_y_calidad.md`
- `docs/04_Arquitectura/01_Vistas_y_patrones.md`
- `docs/09_DevOps/01_Monorepo_Gradle.md`
- `docs/00_Gobierno/03_Matriz_cumplimiento.md`
- `docs/01_Producto/Requisitos_Trazados/RF_INTG.md`
- `docs/01_Producto/Requisitos_Trazados/RNF_MAIN.md`
- `docs/01_Producto/Requisitos_Trazados/RTO_DEV.md`

## Delivery evidence

Commit and PR evidence are pending the ticket close workflow.
