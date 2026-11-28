plugins {
    id("sumak.java-conventions")
    id("org.springframework.boot") version "4.2.0"
    id("io.spring.dependency-management") version "1.1.6"
}

description = "Versioned configuration and effective policy rule service"

dependencies {
    implementation("org.springframework.boot:spring-boot-starter")
    implementation("org.springframework.boot:spring-boot-starter-actuator")
    implementation("org.springframework.boot:spring-boot-starter-webflux")

    testImplementation("org.junit.jupiter:junit-jupiter")
    testImplementation("com.tngtech.archunit:archunit-junit5:1.3.0")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}
