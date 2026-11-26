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

Service modules live under `services/`, and edge components live under
`platform/`. Each module is independently buildable and must communicate with
other domains through versioned contracts rather than runtime project
dependencies.
