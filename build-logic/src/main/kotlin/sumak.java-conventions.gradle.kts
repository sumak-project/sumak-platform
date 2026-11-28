import org.gradle.api.GradleException
import org.gradle.api.artifacts.ProjectDependency

plugins {
    java
    id("com.diffplug.spotless")
}

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}

tasks.withType<JavaCompile>().configureEach {
    options.encoding = "UTF-8"
    options.release = 21
}

tasks.withType<Test>().configureEach {
    useJUnitPlatform()
}

val productionDependencyConfigurations =
    setOf("api", "implementation", "compileOnly", "runtimeOnly")

val architectureBoundaryCheck = tasks.register("architectureBoundaryCheck") {
    group = "verification"
    description =
        "Rejects runtime or compile-time project dependencies between bounded modules."

    doLast {
        val injectedViolation =
            providers.gradleProperty("architectureBoundaryCheck.injectProjectDependency")
                .orNull
        val violations =
            configurations
                .filter { it.name in productionDependencyConfigurations }
                .flatMap { configuration ->
                    configuration.allDependencies
                        .withType(ProjectDependency::class.java)
                        .map { dependency ->
                            "${project.path}:${configuration.name} -> ${dependency.path}"
                        }
                }
                .sorted()
                .toMutableList()

        if (injectedViolation != null) {
            violations += "${project.path}:implementation -> project($injectedViolation) [negative test]"
        }

        if (violations.isNotEmpty()) {
            throw GradleException(
                buildString {
                    appendLine(
                        "Bounded modules must integrate through versioned contract artifacts, " +
                            "not Gradle project dependencies:"
                    )
                    violations.forEach { appendLine(" - $it") }
                }
            )
        }
    }
}

tasks.named("check") {
    dependsOn(architectureBoundaryCheck)
}

spotless {
    ratchetFrom("origin/dev")

    java {
        googleJavaFormat()
        removeUnusedImports()
        trimTrailingWhitespace()
        endWithNewline()
    }
}
