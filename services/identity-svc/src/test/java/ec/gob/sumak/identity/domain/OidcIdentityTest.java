package ec.gob.sumak.identity.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatNullPointerException;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

class OidcIdentityTest {

    @Test
    void preservesIssuerAndSubject() {
        var identity = new OidcIdentity("https://issuer.example/oidc", "staff-123");

        assertThat(identity.issuer()).isEqualTo("https://issuer.example/oidc");
        assertThat(identity.subject()).isEqualTo("staff-123");
    }

    @Test
    void rejectsNullIssuerAndSubject() {
        assertThatNullPointerException().isThrownBy(() -> new OidcIdentity(null, "sub"));
        assertThatNullPointerException().isThrownBy(() -> new OidcIdentity("issuer", null));
    }

    @ParameterizedTest
    @ValueSource(strings = {"", " ", "\t", "\n"})
    void rejectsBlankIssuer(String issuer) {
        assertThatThrownBy(() -> new OidcIdentity(issuer, "sub"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("issuer");
    }

    @ParameterizedTest
    @ValueSource(strings = {"", " ", "\t", "\n"})
    void rejectsBlankSubject(String subject) {
        assertThatThrownBy(() -> new OidcIdentity("issuer", subject))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("subject");
    }

    @Test
    void equalityRequiresBothIssuerAndSubject() {
        var base = new OidcIdentity("issuer-a", "sub-1");

        assertThat(base)
                .isEqualTo(new OidcIdentity("issuer-a", "sub-1"))
                .hasSameHashCodeAs(new OidcIdentity("issuer-a", "sub-1"));
        // issuer isolation: same subject under a different issuer is a different identity
        assertThat(base).isNotEqualTo(new OidcIdentity("issuer-b", "sub-1"));
        assertThat(base).isNotEqualTo(new OidcIdentity("issuer-a", "sub-2"));
    }
}
