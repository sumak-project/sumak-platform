package ec.gob.sumak.identity.application.port;

import java.util.Optional;
import java.util.UUID;

public interface CommandReceiptRepository {
    Optional<UUID> resultFor(UUID commandId);

    void record(UUID commandId, UUID accountId);
}
