package ec.gob.sumak.identity.domain;

import java.time.Instant;
import java.util.Objects;
import java.util.UUID;

public record RoleAssignment(
        UUID id,
        InstitutionalRole role,
        String scopeType,
        String scopeRef,
        Instant validFrom,
        Instant validUntil,
        Instant revokedAt,
        String grantedByRef) {

    public RoleAssignment {
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(role, "role");
        scopeType = requireText(scopeType, "scopeType");
        scopeRef = requireText(scopeRef, "scopeRef");
        Objects.requireNonNull(validFrom, "validFrom");
        grantedByRef = requireText(grantedByRef, "grantedByRef");
        if (validUntil != null && !validUntil.isAfter(validFrom)) {
            throw new IllegalArgumentException("validUntil must be after validFrom");
        }
    }

    public boolean isActiveAt(Instant instant) {
        return revokedAt == null
                && !instant.isBefore(validFrom)
                && (validUntil == null || instant.isBefore(validUntil));
    }

    private static String requireText(String value, String name) {
        Objects.requireNonNull(value, name);
        if (value.isBlank()) {
            throw new IllegalArgumentException(name + " must not be blank");
        }
        return value;
    }
}
