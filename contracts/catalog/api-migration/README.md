# API contract migration matrix

This catalog reconstructs the 162 unique historical `/v1` method/path
combinations as a candidate input for the current SUMAK contract design. It
does not authorize business REST and does not generate executable contracts.

## Files

- `source-routes.tsv` is the tracked historical route inventory and candidate
  owner mapping recovered from Confluence content `6356993`, version 2.
- `overrides.json` is the only place for reviewed row-level decisions. Every
  override must carry a value, status, source, and explanatory note.
- `generate_matrix.py` validates source uniqueness and coverage, then generates
  the JSON evidence matrix and the review-oriented CSV projection.
- `api-migration-matrix.json` is the canonical generated evidence, including
  per-cell provenance.
- `api-migration-matrix.csv` is a generated flat projection containing every
  required value and its evidence status.

Generated files must not be edited manually. Regenerate and verify them with:

```bash
python3 contracts/catalog/api-migration/generate_matrix.py
python3 contracts/catalog/api-migration/generate_matrix.py --check
```

## Evidence semantics

- `EVIDENCED`: directly supported by the cited current authoritative source.
- `CANDIDATE`: recovered or derived input that still requires review.
- `PENDING`: unresolved; it is not approval, implementation, or a passing gate.

The historical route inventory is intentionally `CANDIDATE`. All fields that
cannot be established without a row-level domain decision remain `PENDING`.
Current architecture remains GraphQL for clients, gRPC internally, Kafka for
facts and replay, RabbitMQ for work, WSS for notifications, and HTTP only for
authorized webhooks or technical interfaces.

## Handoff to SCRUM-52

SCRUM-52 remains blocked until every row needed for executable generation has
reviewed values for target operation, ownership, DTO fields, authorization,
idempotency, errors, timeout, retry, version, and test case, and the resulting
package is explicitly approved. This catalog exposes the remaining decisions
without inventing them.
