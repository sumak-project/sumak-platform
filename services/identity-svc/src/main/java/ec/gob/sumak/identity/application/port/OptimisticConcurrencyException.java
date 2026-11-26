package ec.gob.sumak.identity.application.port;

import java.util.UUID;

public final class OptimisticConcurrencyException extends RuntimeException {
    public OptimisticConcurrencyException(String message) {
        super(message);
    }

    public OptimisticConcurrencyException(UUID aggregateId, long expectedVersion) {
        this("identity account %s is no longer at version %d".formatted(aggregateId, expectedVersion));
    }
}
