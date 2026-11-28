# Executable contract package

This package validates the approved v1 protocol policy and deterministically
links the migration matrix, generated catalog, and compatibility baseline. It
does not generate schemas for operations whose target evidence is `PENDING`.

The approved split is GraphQL for clients, gRPC for internal synchronous calls,
Kafka for facts and replay, RabbitMQ for work, WSS for notifications, and HTTP
only for authorized webhooks and technical interfaces.

## Checks

Requires Python 3.10+ and Node.js 20+:

```sh
python3 contracts/catalog/api-migration/generate_matrix.py --check
python3 contracts/executable/tools/generar.py --check
python3 contracts/executable/tools/integraciones.py
python3 contracts/executable/tools/trazabilidad.py
python3 contracts/executable/tools/compatibilidad.py
node contracts/executable/tools/validar.cjs
python3 contracts/executable/tools/revisar_estructura.py
```

A zero-exit `PENDING` result means the check executed successfully, not that an
operation is implemented or compatible. The current catalog has 162 pending
operations and zero executable schemas. Compiler checks therefore remain
`NOT_RUN`, not `PASS`.

Never refresh `catalogo/schemas-baseline.json` automatically. Baseline changes
require explicit versioning review.
