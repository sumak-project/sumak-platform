#!/usr/bin/env node
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const read = (name) => JSON.parse(fs.readFileSync(path.join(root, name), "utf8"));
const requireValue = (condition, message) => { if (!condition) throw new Error(message); };
try {
  const policy = read("catalogo/package-policy.json");
  const baseline = read("catalogo/schemas-baseline.json");
  const catalog = read("generated/contract-catalog.json");
  requireValue(policy.protocols.clients === "GRAPHQL", "clients must use GraphQL");
  requireValue(policy.protocols.internalSync === "GRPC", "internal sync must use gRPC");
  requireValue(policy.protocols.factsReplay === "KAFKA", "facts must use Kafka");
  requireValue(policy.protocols.work === "RABBITMQ", "work must use RabbitMQ");
  requireValue(policy.protocols.http === "AUTHORIZED_WEBHOOKS_AND_TECHNICAL_ONLY", "business REST is forbidden");
  requireValue(baseline.baseline === "v1", "baseline must be v1");
  requireValue(catalog.rowCount === 162 && catalog.entries.length === 162, "catalog must contain 162 rows");
  requireValue(catalog.generatedCount + catalog.pendingCount === 162, "counts must cover every row");
  for (const entry of catalog.entries) {
    if (!entry.executable) requireValue(entry.generationResult === "PENDING", "pending row generated");
  }
  console.log(`${catalog.status}: JSON validation rows=162 generated=${catalog.generatedCount} pending=${catalog.pendingCount}`);
} catch (error) {
  console.error(`FAIL: ${error.message}`);
  process.exit(1);
}
