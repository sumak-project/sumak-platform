package ec.gob.sumak.identity.domain;

import java.util.Objects;

public record OidcIdentity(String issuer, String subject) {
    public OidcIdentity {
        issuer = requireText(issuer, "issuer");
        subject = requireText(subject, "subject");
    }

    private static String requireText(String value, String name) {
        Objects.requireNonNull(value, name);
        if (value.isBlank()) {
            throw new IllegalArgumentException(name + " must not be blank");
        }
        return value;
    }
}
