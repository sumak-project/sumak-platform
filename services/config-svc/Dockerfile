# syntax=docker/dockerfile:1.7

ARG BUILDER_IMAGE=eclipse-temurin:21-jdk-alpine@sha256:c07bb82e004a166b5d3d63b84ad70e2e822f228505e2e0c0b8dfdc2890d22f13
ARG RUNTIME_IMAGE=eclipse-temurin:21-jre-alpine@sha256:5d7689f47d670aca766b9503a70bccc2d73b4eb9221ae8f714ae958313c4ce70

FROM ${BUILDER_IMAGE} AS builder
WORKDIR /workspace

COPY gradlew build.gradle.kts settings.gradle.kts ./
COPY gradle ./gradle
COPY build-logic ./build-logic
COPY services ./services

RUN --mount=type=cache,target=/root/.gradle \
    ./gradlew :services:config-svc:bootJar --no-daemon \
    && cp services/config-svc/build/libs/config-svc-*.jar /workspace/config-svc.jar

FROM ${RUNTIME_IMAGE} AS runtime

RUN addgroup -S -g 10001 sumak \
    && adduser -S -D -H -u 10001 -G sumak sumak

WORKDIR /app
COPY --from=builder --chown=10001:10001 /workspace/config-svc.jar /app/config-svc.jar

ENV JAVA_TOOL_OPTIONS="-XX:InitialRAMPercentage=25.0 -XX:MaxRAMPercentage=75.0 -Djava.io.tmpdir=/tmp"

USER 10001:10001
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/health/live \
    && wget -q -O /dev/null http://127.0.0.1:8080/health/ready \
    && wget -q -O /dev/null http://127.0.0.1:8080/health/startup

ENTRYPOINT ["java", "-jar", "/app/config-svc.jar"]
