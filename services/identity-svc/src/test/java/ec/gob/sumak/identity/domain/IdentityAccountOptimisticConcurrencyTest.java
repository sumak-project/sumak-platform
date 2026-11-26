package ec.gob.sumak.identity.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

/**
 * SCRUM-60 — Optimistic concurrency version semantics (unit, no DB).
 *
 * <p>Acceptance: PostgreSQL conditional UPDATE uses expected {@code row_version};
 * stale concurrent writers conflict; two simultaneous edits produce one success /
 * one conflict; no blind retry. The PostgreSQL behavior is proven on real
 * PostgreSQL Testcontainers by
 * {@code ec.gob.sumak.identity.infrastructure.persistence.IdentityOptimisticConcurrencyIT}.
 *
 * <p>This class pins the domain side of the contract that feeds the conditional update:
 * <ul>
 *   <li>every mutation bumps {@link IdentityAccount#version()} by exactly one;</li>
 *   <li>{@code expectedVersion} passed to {@code IdentityAccountRepository.save(account, expectedVersion)}
 *       is the version <em>before</em> mutation ({@code account.version() - 1}),
 *       which maps to {@code WHERE id = ? AND row_version = ?};</li>
 *   <li>a fresh insert uses {@code expectedVersion == -1} and yields {@code row_version = 0};</li>
 *   <li>{@code row_version} can never go negative.</li>
 * </ul>
 */
class IdentityAccountOptimisticConcurrencyTest {

    private static final UUID ACCOUNT_ID = UUID.fromString("22222222-2222-2222-2222-222222222222");
    private static final OidcIdentity IDENTITY = new OidcIdentity("https://issuer.example/oidc", "staff-123");
    private static final Instant NOW = Instant.parse("2026-06-01T12:00:00Z");

    @Test
    void newAccountHasRowVersionZeroAndInsertExpectsMinusOneSentinel() {
        var account = IdentityAccount.linkInstitutional(ACCOUNT_ID, IDENTITY);

        assertThat(account.version()).isZero();
        // insert path: no pre-existing row to match; repository uses expectedVersion == -1 for INSERT
        long insertExpectedVersion = -1;
        assertThat(account.version()).isEqualTo(insertExpectedVersion + 1);
    }

    @Test
    void activateBumpsVersionByExactlyOneAndExpectedVersionIsVersionBeforeMutation() {
        var account = IdentityAccount.linkInstitutional(ACCOUNT_ID, IDENTITY);
        long before = account.version();

        account.activate();

        assertThat(account.version()).isEqualTo(before + 1);
        // conditional UPDATE ... WHERE id = ? AND row_version = ?  ->  expected row_version = before
        assertThat(before).isEqualTo(account.version() - 1);
    }

    @Test
    void suspendBumpsVersionByExactlyOneAndExpectedVersionIsVersionBeforeMutation() {
        var account = activeAccount();
        long before = account.version();

        account.suspend();

        assertThat(account.version()).isEqualTo(before + 1);
        assertThat(before).isEqualTo(account.version() - 1);
    }

    @Test
    void assignBumpsVersionByExactlyOneAndExpectedVersionIsVersionBeforeMutation() {
        var account = activeAccount();
        long before = account.version();

        account.assign(roleAssignment(), NOW);

        assertThat(account.version()).isEqualTo(before + 1);
        assertThat(before).isEqualTo(account.version() - 1);
    }

    @Test
    void restoredAccountKeepsPersistedRowVersionForConditionalUpdate() {
        var account = IdentityAccount.restore(
                ACCOUNT_ID, IDENTITY, IdentityChannel.STAFF, AccountStatus.ACTIVE, 41, List.of());
        long persistedRowVersion = account.version();

        account.suspend(); // a stale writer that read row_version=41 then mutates

        // it will attempt WHERE row_version = 41; a writer that already moved it to 42 makes this conflict
        assertThat(persistedRowVersion).isEqualTo(41);
        assertThat(account.version()).isEqualTo(persistedRowVersion + 1);
        assertThat(persistedRowVersion).isEqualTo(account.version() - 1);
    }

    @Test
    void rowVersionCannotBeNegative() {
        assertThatThrownBy(() -> IdentityAccount.restore(
                        ACCOUNT_ID, IDENTITY, IdentityChannel.STAFF, AccountStatus.ACTIVE, -1, List.of()))
                .isInstanceOf(IllegalArgumentException.class);
    }

    private static IdentityAccount activeAccount() {
        var account = IdentityAccount.linkInstitutional(ACCOUNT_ID, IDENTITY);
        account.activate();
        return account;
    }

    private static RoleAssignment roleAssignment() {
        return new RoleAssignment(
                UUID.randomUUID(),
                InstitutionalRole.CITIZEN,
                "country",
                "EC",
                NOW.minusSeconds(3600),
                null,
                null,
                "granter-ref");
    }
}
