pluginManagement {
    includeBuild("build-logic")

    repositories {
        gradlePluginPortal()
        mavenCentral()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        mavenCentral()
    }
}

rootProject.name = "sumak-platform"

include(
    ":services:identity-svc",
    ":services:config-svc",
    ":services:citizen-profile-svc",
    ":services:registry-svc",
    ":services:budget-command-svc",
    ":services:budget-query-svc",
    ":services:works-command-svc",
    ":services:works-query-svc",
    ":services:vote-eligibility-svc",
    ":services:vote-ballot-svc",
    ":services:vote-tally-svc",
    ":services:incident-command-svc",
    ":services:incident-query-svc",
    ":services:geo-svc",
    ":services:notification-svc",
    ":services:audit-svc",
    ":services:report-svc",
    ":services:media-svc",
    ":services:search-svc",
    ":services:field-ingest-svc",
    ":services:agent-svc",
    ":services:ledger-svc",
    ":platform:api-gateway",
    ":platform:bff-mobile",
    ":platform:bff-admin",
    ":platform:realtime-gateway",
)
