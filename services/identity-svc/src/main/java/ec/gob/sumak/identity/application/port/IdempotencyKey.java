package ec.gob.sumak.identity.application.port;

import java.util.Objects;
import java.util.UUID;

public record IdempotencyKey(String scopeKey, String operation, UUID commandId) {
    public IdempotencyKey {
        if (Objects.requireNonNull(scopeKey, "scopeKey").isBlank()) {
            throw new IllegalArgumentException("scopeKey must not be blank");
        }
        if (Objects.requireNonNull(operation, "operation").isBlank()) {
            throw new IllegalArgumentException("operation must not be blank");
        }
        Objects.requireNonNull(commandId, "commandId");
    }
}
