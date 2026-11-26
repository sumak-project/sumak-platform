package ec.gob.sumak.identity.application.port;

import java.util.Objects;
import java.util.UUID;

public record CommandReceipt(IdempotencyKey key, String requestDigestSha256, UUID resourceRef) {
    public CommandReceipt {
        Objects.requireNonNull(key, "key");
        Objects.requireNonNull(requestDigestSha256, "requestDigestSha256");
        Objects.requireNonNull(resourceRef, "resourceRef");
    }
}
