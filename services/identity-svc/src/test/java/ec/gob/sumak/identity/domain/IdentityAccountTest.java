package ec.gob.sumak.identity.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatExceptionOfType;
import static org.assertj.core.api.Assertions.assertThatNullPointerException;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class IdentityAccountTest {

    private static final UUID ACCOUNT_ID = UUID.randomUUID();
    private static final OidcIdentity IDENTITY = new OidcIdentity("https://issuer.example/oidc", "staff-123");
    private static final Instant NOW = Instant.parse("2026-06-01T12:00:00Z");

    private static RoleAssignment assignment(InstitutionalRole role, String scopeType, String scopeRef) {
        return new RoleAssignment(
                UUID.randomUUID(), role, scopeType, scopeRef, NOW.minusSeconds(3600), null, null, "granter-ref");
    }

    // ---- construction / invariants ----

    @Test
    void linkInstitutionalStartsPendingStaffWithVersionZeroAndNoAssignments() {
        var account = IdentityAccount.linkInstitutional(ACCOUNT_ID, IDENTITY);

        assertThat(account.id()).isEqualTo(ACCOUNT_ID);
        assertThat(account.oidcIdentity()).isEqualTo(IDENTITY);
        assertThat(account.channel()).isEqualTo(IdentityChannel.STAFF);
        assertThat(account.status()).isEqualTo(AccountStatus.PENDING);
        assertThat(account.version()).isZero();
        assertThat(account.assignments()).isEmpty();
    }

    @Test
    void rejectsNullRequiredComponents() {
        assertThatNullPointerException().isThrownBy(() -> IdentityAccount.linkInstitutional(null, IDENTITY));
        assertThatNullPointerException().isThrownBy(() -> IdentityAccount.linkInstitutional(ACCOUNT_ID, null));
        assertThatNullPointerException()
                .isThrownBy(() -> IdentityAccount.restore(ACCOUNT_ID, null, IdentityChannel.STAFF, AccountStatus.ACTIVE, 0, List.of()));
        assertThatNullPointerException()
                .isThrownBy(() -> IdentityAccount.restore(ACCOUNT_ID, IDENTITY, null, AccountStatus.ACTIVE, 0, List.of()));
        assertThatNullPointerException()
                .isThrownBy(() -> IdentityAccount.restore(ACCOUNT_ID, IDENTITY, IdentityChannel.STAFF, null, 0, List.of()));
        assertThatNullPointerException()
                .isThrownBy(() -> IdentityAccount.restore(ACCOUNT_ID, IDENTITY, IdentityChannel.STAFF, AccountStatus.ACTIVE, 0, null));
    }

    @Test
    void rejectsNegativeVersion() {
        assertThatThrownBy(() -> IdentityAccount.restore(ACCOUNT_ID, IDENTITY, IdentityChannel.STAFF, AccountStatus.ACTIVE, -1, List.of()))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("version");
    }

    @Test
    void restorePreservesStateAndDefensivelyCopiesAssignments() {
        var granted = assignment(InstitutionalRole.CITIZEN, "country", "EC");
        var source = new java.util.ArrayList<RoleAssignment>();
        source.add(granted);

        var account = IdentityAccount.restore(ACCOUNT_ID, IDENTITY, IdentityChannel.CITIZEN, AccountStatus.ACTIVE, 7, source);
        source.clear();

        assertThat(account.channel()).isEqualTo(IdentityChannel.CITIZEN);
        assertThat(account.status()).isEqualTo(AccountStatus.ACTIVE);
        assertThat(account.version()).isEqualTo(7);
        assertThat(account.assignments()).containsExactly(granted);
    }

    @Test
    void assignmentsListIsUnmodifiable() {
        var account = IdentityAccount.linkInstitutional(ACCOUNT_ID, IDENTITY);

        assertThatExceptionOfType(UnsupportedOperationException.class)
                .isThrownBy(() -> account.assignments().add(assignment(InstitutionalRole.CITIZEN, "country", "EC")));
    }

    // ---- state transitions / concurrency version ----

    @Test
    void activateMovesPendingToActiveAndIncrementsVersion() {
        var account = IdentityAccount.linkInstitutional(ACCOUNT_ID, IDENTITY);

        account.activate();

        assertThat(account.status()).isEqualTo(AccountStatus.ACTIVE);
        assertThat(account.version()).isEqualTo(1);
    }

    @Test
    void activateOnActiveAccountIsIdempotentButStillBumpsVersion() {
        var account = activeAccount();
        long before = account.version();

        account.activate();

        assertThat(account.status()).isEqualTo(AccountStatus.ACTIVE);
        assertThat(account.version()).isEqualTo(before + 1);
    }

    @Test
    void suspendMarksSuspendedAndIncrementsVersion() {
        var account = activeAccount();
        long before = account.version();

        account.suspend();

        assertThat(account.status()).isEqualTo(AccountStatus.SUSPENDED);
        assertThat(account.version()).isEqualTo(before + 1);
    }

    @Test
    void suspendedAccountCannotBeActivatedWithoutReview() {
        var account = activeAccount();
        account.suspend();
        long versionAtSuspension = account.version();

        assertThatThrownBy(account::activate)
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("suspended");
        assertThat(account.status()).isEqualTo(AccountStatus.SUSPENDED);
        assertThat(account.version()).isEqualTo(versionAtSuspension);
    }

    // ---- role assignment ----

    @Test
    void assignRequiresActiveAccount() {
        var pending = IdentityAccount.linkInstitutional(ACCOUNT_ID, IDENTITY);

        assertThatThrownBy(() -> pending.assign(assignment(InstitutionalRole.CITIZEN, "country", "EC"), NOW))
                .isInstanceOf(IllegalStateException.class);

        var suspended = activeAccount();
        suspended.suspend();
        assertThatThrownBy(() -> suspended.assign(assignment(InstitutionalRole.CITIZEN, "country", "EC"), NOW))
                .isInstanceOf(IllegalStateException.class);
    }

    @Test
    void assignRejectsNullArguments() {
        var account = activeAccount();

        assertThatNullPointerException().isThrownBy(() -> account.assign(null, NOW));
        assertThatNullPointerException().isThrownBy(() -> account.assign(assignment(InstitutionalRole.CITIZEN, "country", "EC"), null));
    }

    @Test
    void assignRejectsDuplicateActiveRoleAndScope() {
        var account = activeAccount();
        account.assign(assignment(InstitutionalRole.CITIZEN, "country", "EC"), NOW);
        long versionAfterFirst = account.version();

        assertThatThrownBy(() -> account.assign(assignment(InstitutionalRole.CITIZEN, "country", "EC"), NOW))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("already exists");
        assertThat(account.version()).isEqualTo(versionAfterFirst);
    }

    @Test
    void assignAllowsSameRoleOnDifferentScope() {
        var account = activeAccount();
        account.assign(assignment(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, "municipality", "mun-001"), NOW);
        account.assign(assignment(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, "municipality", "mun-002"), NOW);

        assertThat(account.assignments()).hasSize(2);
    }

    @Test
    void assignAllowsSameScopeWithDifferentRole() {
        var account = activeAccount();
        account.assign(assignment(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, "municipality", "mun-001"), NOW);
        account.assign(assignment(InstitutionalRole.INCIDENTS_AND_COMPLAINTS_OPERATOR, "municipality", "mun-001"), NOW);

        assertThat(account.assignments()).hasSize(2);
    }

    @Test
    void assignSuccessIncrementsVersion() {
        var account = activeAccount();
        long before = account.version();

        account.assign(assignment(InstitutionalRole.CITIZEN, "country", "EC"), NOW);

        assertThat(account.version()).isEqualTo(before + 1);
    }

    // ---- authorization ----

    @Test
    void authorizedOnlyWhenActiveMatchingRoleScopeAndInsideWindow() {
        var account = activeAccount();
        account.assign(assignment(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, "municipality", "mun-001"), NOW);

        assertThat(account.isAuthorized(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, "municipality", "mun-001", NOW)).isTrue();
        assertThat(account.isAuthorized(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, "municipality", "mun-001", NOW.plusSeconds(60))).isTrue();
    }

    @Test
    void deniesWrongRoleScopeOrCase() {
        var account = activeAccount();
        account.assign(assignment(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, "municipality", "mun-001"), NOW);

        assertThat(account.isAuthorized(InstitutionalRole.CITIZEN, "municipality", "mun-001", NOW)).isFalse();
        assertThat(account.isAuthorized(InstitutionalRole.SUPER_ADMINISTRATOR, "municipality", "mun-001", NOW)).isFalse();
        assertThat(account.isAuthorized(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, "municipality", "mun-002", NOW)).isFalse();
        assertThat(account.isAuthorized(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, "Municipality", "mun-001", NOW)).isFalse();
        assertThat(account.isAuthorized(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, "municipality", "MUN-001", NOW)).isFalse();
    }

    @Test
    void deniesWhenNotActive() {
        var pending = IdentityAccount.linkInstitutional(ACCOUNT_ID, IDENTITY);
        assertThat(pending.isAuthorized(InstitutionalRole.CITIZEN, "country", "EC", NOW)).isFalse();

        var suspended = activeAccount();
        suspended.assign(assignment(InstitutionalRole.CITIZEN, "country", "EC"), NOW);
        suspended.suspend();
        assertThat(suspended.isAuthorized(InstitutionalRole.CITIZEN, "country", "EC", NOW)).isFalse();
    }

    @Test
    void deniesOutsideValidityWindow() {
        var account = activeAccount();
        var windowed = new RoleAssignment(
                UUID.randomUUID(), InstitutionalRole.CITIZEN, "country", "EC",
                NOW, NOW.plusSeconds(3600), null, "granter-ref");
        account.assign(windowed, NOW);

        assertThat(account.isAuthorized(InstitutionalRole.CITIZEN, "country", "EC", NOW.minusSeconds(1))).isFalse();
        assertThat(account.isAuthorized(InstitutionalRole.CITIZEN, "country", "EC", NOW)).isTrue();
        assertThat(account.isAuthorized(InstitutionalRole.CITIZEN, "country", "EC", NOW.plusSeconds(3600))).isFalse();
    }

    private static IdentityAccount activeAccount() {
        var account = IdentityAccount.linkInstitutional(ACCOUNT_ID, IDENTITY);
        account.activate();
        return account;
    }
}
