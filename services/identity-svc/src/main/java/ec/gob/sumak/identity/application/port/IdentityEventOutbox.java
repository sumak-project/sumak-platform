package ec.gob.sumak.identity.application.port;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;

public interface IdentityEventOutbox {
    void append(
            UUID eventId,
            String eventType,
            int schemaVersion,
            UUID aggregateRef,
            long aggregateVersion,
            Instant occurredAt,
            Map<String, String> payload);
}
