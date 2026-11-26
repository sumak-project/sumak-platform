package ec.gob.sumak.identity.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatNullPointerException;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Instant;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class RoleAssignmentTest {

    private static final UUID ID = UUID.randomUUID();
    private static final Instant FROM = Instant.parse("2026-01-01T00:00:00Z");
    private static final Instant UNTIL = Instant.parse("2026-02-01T00:00:00Z");

    private static RoleAssignment assignment(Instant validUntil, Instant revokedAt) {
        return new RoleAssignment(
                ID,
                InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR,
                "municipality",
                "mun-001",
                FROM,
                validUntil,
                revokedAt,
                "granter-ref");
    }

    @Test
    void rejectsNullRequiredComponents() {
        assertThatNullPointerException()
                .isThrownBy(() -> new RoleAssignment(null, InstitutionalRole.CITIZEN, "s", "r", FROM, null, null, "g"));
        assertThatNullPointerException()
                .isThrownBy(() -> new RoleAssignment(ID, null, "s", "r", FROM, null, null, "g"));
        assertThatNullPointerException()
                .isThrownBy(() -> new RoleAssignment(ID, InstitutionalRole.CITIZEN, "s", "r", null, null, null, "g"));
    }

    @Test
    void rejectsBlankScopeAndGranter() {
        assertThatThrownBy(() -> new RoleAssignment(ID, InstitutionalRole.CITIZEN, " ", "r", FROM, null, null, "g"))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new RoleAssignment(ID, InstitutionalRole.CITIZEN, "s", "", FROM, null, null, "g"))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> new RoleAssignment(ID, InstitutionalRole.CITIZEN, "s", "r", FROM, null, null, " "))
                .isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void validUntilMustBeStrictlyAfterValidFrom() {
        assertThatThrownBy(() -> assignment(FROM, null)).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> assignment(FROM.minusSeconds(1), null)).isInstanceOf(IllegalArgumentException.class);
        assertThat(assignment(FROM.plusSeconds(1), null).validUntil()).isEqualTo(FROM.plusSeconds(1));
    }

    @Test
    void activeWindowIsInclusiveAtStartExclusiveAtEnd() {
        var assignment = assignment(UNTIL, null);

        assertThat(assignment.isActiveAt(FROM)).isTrue();
        assertThat(assignment.isActiveAt(FROM.minusSeconds(1))).isFalse();
        assertThat(assignment.isActiveAt(UNTIL.minusSeconds(1))).isTrue();
        assertThat(assignment.isActiveAt(UNTIL)).isFalse();
        assertThat(assignment.isActiveAt(UNTIL.plusSeconds(1))).isFalse();
    }

    @Test
    void openEndedAssignmentStaysActive() {
        var assignment = assignment(null, null);

        assertThat(assignment.isActiveAt(FROM)).isTrue();
        assertThat(assignment.isActiveAt(Instant.parse("2999-01-01T00:00:00Z"))).isTrue();
    }

    @Test
    void revokedAssignmentIsNeverActive() {
        var revoked = assignment(null, FROM.plusSeconds(10));

        // domain treats any non-null revokedAt as inactive, regardless of window
        assertThat(revoked.isActiveAt(FROM)).isFalse();
        assertThat(revoked.isActiveAt(FROM.plusSeconds(10))).isFalse();
        assertThat(revoked.isActiveAt(FROM.plusSeconds(11))).isFalse();
    }
}
