# SUMAK logical API gateway

This module is the Java/Spring edge component behind the DEV ALB. It starts
with no business routes: client operations will be added through bounded
GraphQL tickets, while internal calls must use approved versioned protocols.

The only unauthenticated HTTP operations are technical:

- `GET /health`
- `GET /health/live`
- `GET /health/ready`
- `GET /health/startup`
- `GET /version`

Every other request is denied until an explicitly reviewed route and
authentication policy are introduced.

## Local validation

```bash
./gradlew :platform:api-gateway:check
helm lint infra/helm/service \
  --values config/dev/api-gateway-values.yaml
helm template api-gateway infra/helm/service \
  --namespace sumak-dev \
  --values config/dev/api-gateway-values.yaml
```

The DEV image repository and digest are intentionally non-runnable
placeholders. An approved immutable image is required before deployment.
EKS, ALB target health, DNS, TLS, and WSS runtime validation remain blocked by
their infrastructure prerequisites; local checks do not establish deployment
readiness.
