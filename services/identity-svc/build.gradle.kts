plugins {
    id("sumak.java-conventions")
}

description = "Institutional identity and scoped authorization service"

dependencies {
    testImplementation(platform("org.junit:junit-bom:5.10.2"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    testImplementation("org.assertj:assertj-core:3.25.3")
    testImplementation("com.tngtech.archunit:archunit-junit5:1.3.0")

    // Integration gate: PostgreSQL Testcontainers + Flyway migration validation (requires Docker at runtime)
    testImplementation("org.testcontainers:testcontainers:1.21.4")
    testImplementation("org.testcontainers:junit-jupiter:1.21.4")
    testImplementation("org.testcontainers:postgresql:1.21.4")
    testImplementation("org.flywaydb:flyway-core:9.22.3")
    testRuntimeOnly("org.postgresql:postgresql:42.7.3")
}
