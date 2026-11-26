package ec.gob.sumak.identity.infrastructure.persistence;

import ec.gob.sumak.identity.application.port.IdentityEventOutbox;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.Comparator;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.stream.Collectors;

public final class JdbcIdentityEventOutbox implements IdentityEventOutbox {
    private static final String INSERT = """
            INSERT INTO outbox_event (
                id, event_type, schema_version, aggregate_ref, aggregate_version, occurred_at, payload
            ) VALUES (?, ?, ?, ?, ?, ?, ?::jsonb)
            """;

    private final JdbcIdentityTransaction transactions;

    public JdbcIdentityEventOutbox(JdbcIdentityTransaction transactions) {
        this.transactions = Objects.requireNonNull(transactions, "transactions");
    }

    @Override
    public void append(
            UUID eventId,
            String eventType,
            int schemaVersion,
            UUID aggregateRef,
            long aggregateVersion,
            Instant occurredAt,
            Map<String, String> payload) {
        try (var statement = transactions.connection().prepareStatement(INSERT)) {
            statement.setObject(1, Objects.requireNonNull(eventId, "eventId"));
            statement.setString(2, Objects.requireNonNull(eventType, "eventType"));
            statement.setInt(3, schemaVersion);
            statement.setObject(4, Objects.requireNonNull(aggregateRef, "aggregateRef"));
            statement.setLong(5, aggregateVersion);
            statement.setTimestamp(6, Timestamp.from(Objects.requireNonNull(occurredAt, "occurredAt")));
            statement.setString(7, toJson(payload));
            statement.executeUpdate();
        } catch (SQLException failure) {
            throw new IllegalStateException("failed to append identity outbox event", failure);
        }
    }

    private static String toJson(Map<String, String> payload) {
        Objects.requireNonNull(payload, "payload");
        return payload.entrySet().stream()
                .sorted(Comparator.comparing(Map.Entry::getKey))
                .map(entry -> "\"" + escape(entry.getKey()) + "\":\"" + escape(entry.getValue()) + "\"")
                .collect(Collectors.joining(",", "{", "}"));
    }

    private static String escape(String value) {
        return Objects.requireNonNull(value, "payload value")
                .replace("\\", "\\\\")
                .replace("\"", "\\\"");
    }
}
