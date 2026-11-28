# SUMAK Platform

SUMAK is organized as a Gradle monorepo targeting Java 21. The repository
currently contains the project skeleton; business services are introduced by
their own bounded Jira tickets.

## Local validation

Prerequisite: JDK 21.

```bash
./gradlew check
python3 -m unittest discover -s tests -v
```

The root `check` task aggregates every module's formatting, compilation, and
unit-test gates. Formatting is enforced incrementally against `origin/dev` to
avoid rewriting untouched historical sources. Run a single module selectively
when iterating:

```bash
./gradlew :services:identity-svc:spotlessCheck
./gradlew :services:identity-svc:compileJava
./gradlew :services:identity-svc:test
```

Service modules live under `services/`, and edge components live under
`platform/`. Each module is independently buildable and must communicate with
other domains through versioned contracts rather than runtime project
dependencies.
