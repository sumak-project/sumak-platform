package ec.gob.sumak.identity.security;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import ec.gob.sumak.identity.domain.AccountStatus;
import ec.gob.sumak.identity.domain.IdentityAccount;
import ec.gob.sumak.identity.domain.IdentityChannel;
import ec.gob.sumak.identity.domain.InstitutionalRole;
import ec.gob.sumak.identity.domain.OidcIdentity;
import ec.gob.sumak.identity.domain.RoleAssignment;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

/**
 * Security gate (bounded, no AWS / no real secrets / no real PII):
 * RBAC/ABAC denial, issuer/audience-environment isolation, unauthorized access denial.
 * Authentication itself has no infrastructure adapter in this bounded change -> NOT_RUN at gate level.
 */
class AuthorizationDenialTest {

    private static final Instant NOW = Instant.parse("2026-06-01T12:00:00Z");
    private static final String SCOPE_TYPE = "municipality";
    private static final String SCOPE_REF = "mun-001";

    // synthetic, non-real identities only
    private static final OidcIdentity STAFF = new OidcIdentity("https://issuer.example/oidc", "synthetic-staff-1");

    @Test
    void suspendedAccountIsDeniedEverything() {
        var account = activeAdmin();
        account.suspend();

        assertThat(account.isAuthorized(InstitutionalRole.SUPER_ADMINISTRATOR, SCOPE_TYPE, SCOPE_REF, NOW)).isFalse();
        assertThat(account.isAuthorized(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, SCOPE_TYPE, SCOPE_REF, NOW)).isFalse();
    }

    @Test
    void pendingAccountIsDeniedEverything() {
        var account = IdentityAccount.restore(
                UUID.randomUUID(), STAFF, IdentityChannel.STAFF, AccountStatus.PENDING, 0,
                List.of(adminAssignment()));

        assertThat(account.isAuthorized(InstitutionalRole.SUPER_ADMINISTRATOR, SCOPE_TYPE, SCOPE_REF, NOW)).isFalse();
    }

    @Test
    void roleEscalationIsDenied() {
        var account = activeAdmin(); // has WORKS_AND_FINANCE_ADMINISTRATOR on SCOPE

        // cannot pivot to higher-privilege role
        assertThat(account.isAuthorized(InstitutionalRole.SUPER_ADMINISTRATOR, SCOPE_TYPE, SCOPE_REF, NOW)).isFalse();
        // cannot pivot to another scoped role
        assertThat(account.isAuthorized(InstitutionalRole.INCIDENTS_AND_COMPLAINTS_OPERATOR, SCOPE_TYPE, SCOPE_REF, NOW)).isFalse();
    }

    @Test
    void scopeIsolationIsDeniedAcrossResources() {
        var account = activeAdmin();

        // no access to a different resource in the same scope type
        assertThat(account.isAuthorized(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, SCOPE_TYPE, "mun-002", NOW)).isFalse();
        // no access to a different scope type
        assertThat(account.isAuthorized(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, "country", SCOPE_REF, NOW)).isFalse();
        // no wildcard / prefix matching
        assertThat(account.isAuthorized(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, SCOPE_TYPE, "mun-", NOW)).isFalse();
        assertThat(account.isAuthorized(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, SCOPE_TYPE, SCOPE_REF + "/child", NOW)).isFalse();
    }

    @Test
    void expiredAndRevokedAssignmentsAreDenied() {
        var expired = new RoleAssignment(
                UUID.randomUUID(), InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, SCOPE_TYPE, SCOPE_REF,
                NOW.minusSeconds(7200), NOW.minusSeconds(1), null, "granter-ref");
        var revoked = new RoleAssignment(
                UUID.randomUUID(), InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, SCOPE_TYPE, SCOPE_REF,
                NOW.minusSeconds(7200), null, NOW.minusSeconds(60), "granter-ref");

        var withExpired = IdentityAccount.restore(UUID.randomUUID(), STAFF, IdentityChannel.STAFF, AccountStatus.ACTIVE, 0, List.of(expired));
        var withRevoked = IdentityAccount.restore(UUID.randomUUID(), STAFF, IdentityChannel.STAFF, AccountStatus.ACTIVE, 0, List.of(revoked));

        assertThat(withExpired.isAuthorized(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, SCOPE_TYPE, SCOPE_REF, NOW)).isFalse();
        assertThat(withRevoked.isAuthorized(InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, SCOPE_TYPE, SCOPE_REF, NOW)).isFalse();
    }

    @Test
    void assigningRolesRequiresActiveAccount() {
        var suspended = activeAdmin();
        suspended.suspend();

        // privilege grant on a non-active account is rejected (no self-escalation while suspended)
        assertThatThrownBy(() -> suspended.assign(adminAssignment(), NOW)).isInstanceOf(IllegalStateException.class);

        var pending = IdentityAccount.linkInstitutional(UUID.randomUUID(), STAFF);
        assertThatThrownBy(() -> pending.assign(adminAssignment(), NOW)).isInstanceOf(IllegalStateException.class);
    }

    @Test
    void suspendedAccountCannotBeSilentlyReactivated() {
        var account = activeAdmin();
        account.suspend();

        assertThatThrownBy(account::activate).isInstanceOf(IllegalStateException.class);
        assertThat(account.status()).isEqualTo(AccountStatus.SUSPENDED);
    }

    @Test
    void issuerIsolationSeparatesIdentities() {
        // same subject under a different issuer is a different principal (environment/issuer isolation)
        var issuerA = new OidcIdentity("https://issuer-a.example", "same-subject");
        var issuerB = new OidcIdentity("https://issuer-b.example", "same-subject");

        assertThat(issuerA).isNotEqualTo(issuerB);

        var accountA = IdentityAccount.linkInstitutional(UUID.randomUUID(), issuerA);
        var accountB = IdentityAccount.linkInstitutional(UUID.randomUUID(), issuerB);
        assertThat(accountA.oidcIdentity()).isNotEqualTo(accountB.oidcIdentity());
        assertThat(accountA.id()).isNotEqualTo(accountB.id());
    }

    private static IdentityAccount activeAdmin() {
        var account = IdentityAccount.linkInstitutional(UUID.randomUUID(), STAFF);
        account.activate();
        account.assign(adminAssignment(), NOW.minusSeconds(60));
        return account;
    }

    private static RoleAssignment adminAssignment() {
        return new RoleAssignment(
                UUID.randomUUID(), InstitutionalRole.WORKS_AND_FINANCE_ADMINISTRATOR, SCOPE_TYPE, SCOPE_REF,
                NOW.minusSeconds(3600), null, null, "granter-ref");
    }
}
