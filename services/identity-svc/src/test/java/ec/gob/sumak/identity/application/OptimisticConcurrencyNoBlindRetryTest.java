package ec.gob.sumak.identity.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import ec.gob.sumak.identity.application.port.CommandReceipt;
import ec.gob.sumak.identity.application.port.CommandReceiptRepository;
import ec.gob.sumak.identity.application.port.IdempotencyKey;
import ec.gob.sumak.identity.application.port.IdentityAccountRepository;
import ec.gob.sumak.identity.application.port.IdentityEventOutbox;
import ec.gob.sumak.identity.application.port.OptimisticConcurrencyException;
import ec.gob.sumak.identity.domain.IdentityAccount;
import ec.gob.sumak.identity.domain.OidcIdentity;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.Test;

/**
 * SCRUM-60 — Optimistic concurrency: no blind retry (unit, in-memory fakes, no DB).
 *
 * <p>Acceptance: stale concurrent writers conflict; two simultaneous edits produce
 * one success / one conflict; <strong>no blind retry</strong>. A conflicting write
 * must surface {@link OptimisticConcurrencyException} to the caller; the port is
 * invoked exactly once; no automatic re-read + re-apply + retry; no retry with a
 * different version; no fallback; no partial downstream effects.
 *
 * <p>Docs: "Retry sólo comando seguro" (docs/04_Arquitectura/01_Vistas_y_patrones.md
 * — Lock optimista) and "no reintentar I/O bajo transacción". A caller that wants
 * to retry must re-read state and re-issue a NEW command explicitly (and, for
 * LinkInstitutionalUser, replay is then served by the idempotency record).
 */
class OptimisticConcurrencyNoBlindRetryTest {

    private static final Instant FIXED_NOW = Instant.parse("2026-06-01T12:00:00Z");
    private static final Clock FIXED_CLOCK = Clock.fixed(FIXED_NOW, ZoneOffset.UTC);
    private static final String ISSUER = "https://issuer.example/oidc";
    private static final String SUBJECT = "staff-123";

    @Test
    void concurrentModificationSurfacesConflictAndSaveIsAttemptedExactlyOnce() {
        var accounts = new CountingConflictRepository();
        var receipts = new NoopReceiptRepository();
        var outbox = new RecordingOutbox();
        var service = new LinkInstitutionalUserService(accounts, receipts, outbox, FIXED_CLOCK);

        assertThatThrownBy(() -> service.link(ISSUER, SUBJECT, UUID.randomUUID()))
                .isInstanceOf(OptimisticConcurrencyException.class);

        // no blind retry: exactly one save attempt
        assertThat(accounts.saveAttempts).isEqualTo(1);
        // no re-read + re-apply loop before giving up: identity checked once, no re-read after conflict
        assertThat(accounts.existsByOidcIdentityCalls).isEqualTo(1);
        assertThat(accounts.findByIdCalls).isZero();
        // no partial effects leak outside the (rolled-back) transaction
        assertThat(outbox.appended).isEmpty();
        assertThat(receipts.recorded).isEmpty();
    }

    @Test
    void conflictIsNotSwallowedAsIdempotentSuccessOrAlreadyLinked() {
        var accounts = new CountingConflictRepository();
        var service = new LinkInstitutionalUserService(
                accounts, new NoopReceiptRepository(), new RecordingOutbox(), FIXED_CLOCK);

        // conflict must NOT be translated into a silent replay/success...
        assertThatThrownBy(() -> service.link(ISSUER, SUBJECT, UUID.randomUUID()))
                .isInstanceOf(OptimisticConcurrencyException.class)
                // ...nor masked as the domain "already linked" error
                .hasMessageNotContaining("already linked");
        assertThat(accounts.saveAttempts).isEqualTo(1);
    }

    // ---- fakes ----

    private static final class CountingConflictRepository implements IdentityAccountRepository {
        int saveAttempts;
        int findByIdCalls;
        int existsByOidcIdentityCalls;

        @Override
        public Optional<IdentityAccount> findById(UUID accountId) {
            findByIdCalls++;
            return Optional.empty();
        }

        @Override
        public boolean existsByOidcIdentity(OidcIdentity identity) {
            existsByOidcIdentityCalls++;
            return false;
        }

        @Override
        public void save(IdentityAccount account, long expectedVersion) {
            saveAttempts++;
            throw new OptimisticConcurrencyException(
                    "conditional update affected 0 rows; expected row_version=" + expectedVersion);
        }
    }

    private static final class NoopReceiptRepository implements CommandReceiptRepository {
        final List<CommandReceipt> recorded = new ArrayList<>();

        @Override
        public Optional<CommandReceipt> findReceipt(IdempotencyKey key) {
            return Optional.empty();
        }

        @Override
        public void record(IdempotencyKey key, String requestDigestSha256, UUID resourceRef) {
            recorded.add(new CommandReceipt(key, requestDigestSha256, resourceRef));
        }
    }

    private static final class RecordingOutbox implements IdentityEventOutbox {
        final List<Map<String, String>> appended = new ArrayList<>();

        @Override
        public void append(
                UUID eventId,
                String eventType,
                int schemaVersion,
                UUID aggregateRef,
                long aggregateVersion,
                Instant occurredAt,
                Map<String, String> payload) {
            appended.add(Map.copyOf(payload));
        }
    }
}
