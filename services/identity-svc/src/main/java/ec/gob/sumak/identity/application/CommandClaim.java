package ec.gob.sumak.identity.application;

import java.util.Objects;
import java.util.UUID;

public sealed interface CommandClaim permits CommandClaim.Acquired, CommandClaim.Completed {
    record Acquired() implements CommandClaim {}

    record Completed(UUID resourceRef) implements CommandClaim {
        public Completed {
            Objects.requireNonNull(resourceRef, "resourceRef");
        }
    }
}
