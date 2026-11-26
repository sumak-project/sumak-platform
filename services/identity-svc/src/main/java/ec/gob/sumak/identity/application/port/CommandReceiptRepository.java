package ec.gob.sumak.identity.application.port;

import ec.gob.sumak.identity.application.CommandClaim;
import ec.gob.sumak.identity.application.CommandKey;
import java.util.Optional;
import java.util.UUID;

public interface CommandReceiptRepository {
    default CommandClaim claim(CommandKey key, String requestDigest) {
        var idempotencyKey = new IdempotencyKey(key.scopeKey(), key.operation(), key.commandId());
        var receipt = findReceipt(idempotencyKey);
        if (receipt.isEmpty()) {
            return new CommandClaim.Acquired();
        }
        if (!receipt.get().requestDigestSha256().isEmpty()
                && !receipt.get().requestDigestSha256().equals(requestDigest)) {
            throw new IdempotencyConflictException(
                    "command key was already used with a different request digest");
        }
        return new CommandClaim.Completed(receipt.get().resourceRef());
    }

    default void complete(CommandKey key, String requestDigest, UUID resourceRef) {
        record(new IdempotencyKey(key.scopeKey(), key.operation(), key.commandId()), requestDigest, resourceRef);
    }

    default Optional<CommandReceipt> findReceipt(IdempotencyKey key) {
        return resultFor(key.commandId()).map(resourceRef -> new CommandReceipt(key, "", resourceRef));
    }

    default void record(IdempotencyKey key, String requestDigestSha256, UUID resourceRef) {
        record(key.commandId(), resourceRef);
    }

    default Optional<UUID> resultFor(UUID commandId) {
        return Optional.empty();
    }

    default void record(UUID commandId, UUID resourceRef) {
        throw new UnsupportedOperationException("receipt repository must implement record");
    }
}
