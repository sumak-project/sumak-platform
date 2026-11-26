package ec.gob.sumak.identity.application;

import java.util.Objects;
import java.util.UUID;

public record LinkInstitutionalUserCommand(
        String scopeKey, String issuer, String staffSubject, UUID commandId) {
    public LinkInstitutionalUserCommand {
        if (Objects.requireNonNull(scopeKey, "scopeKey").isBlank()) {
            throw new IllegalArgumentException("scopeKey must not be blank");
        }
        Objects.requireNonNull(issuer, "issuer");
        Objects.requireNonNull(staffSubject, "staffSubject");
        Objects.requireNonNull(commandId, "commandId");
    }
}
