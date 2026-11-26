package ec.gob.sumak.identity.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import ec.gob.sumak.identity.application.port.CommandReceipt;
import ec.gob.sumak.identity.application.port.CommandReceiptRepository;
import ec.gob.sumak.identity.application.port.IdempotencyConflictException;
import ec.gob.sumak.identity.application.port.IdempotencyKey;
import ec.gob.sumak.identity.application.port.IdentityAccountRepository;
import ec.gob.sumak.identity.application.port.IdentityEventOutbox;
import ec.gob.sumak.identity.application.port.OptimisticConcurrencyException;
import ec.gob.sumak.identity.domain.IdentityAccount;
import ec.gob.sumak.identity.domain.OidcIdentity;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

/**
 * SCRUM-60 — Idempotency for LinkInstitutionalUser (unit, JUnit 5 + AssertJ, in-memory fakes, no AWS, no DB).
 *
 * <p>Acceptance under test (see docs/10_Datos/identity-svc.md `idempotency_record`,
 * "Misma clave y digest devuelve resultado, diferente digest conflicto; efecto y registro atómicos"):
 *
 * <ol>
 *   <li>key = scope + operation + commandId
 *       ({@code scope_key + operation + command_id}; PK(scope_key, operation, command_id)),
 *       scope key = {@value LinkInstitutionalUserService#IDEMPOTENCY_SCOPE_KEY},
 *       operation = {@value LinkInstitutionalUserService#IDEMPOTENCY_OPERATION_LINK_INSTITUTIONAL_USER};</li>
 *   <li>same key + same SHA-256 request digest returns the original result
 *       without duplicate account or outbox;</li>
 *   <li>same key + different digest conflicts
 *       ({@link IdempotencyConflictException});</li>
 *   <li>request digest is lowercase hex SHA-256 (char(64)) of the canonical request
 *       ({@code issuer + "\n" + staffSubject}, UTF-8);</li>
 *   <li>no duplicate account / outbox / idempotency record on replay;</li>
 *   <li>no blind retry on any failure path.</li>
 * </ol>
 *
 * <p>NOTE: effect + outbox + idempotency commit atomically in ONE transaction.
 * That is an infrastructure guarantee proven on real PostgreSQL by
 * {@code ec.gob.sumak.identity.infrastructure.persistence.IdentityIdempotencyAtomicityIT};
 * in-memory fakes here verify application ordering + exactly-once calls, not DB atomicity.
 */
class LinkInstitutionalUserIdempotencyTest {

    private static final Instant FIXED_NOW = Instant.parse("2026-06-01T12:00:00Z");
    private static final Clock FIXED_CLOCK = Clock.fixed(FIXED_NOW, ZoneOffset.UTC);
    private static final String ISSUER = "https://issuer.example/oidc";
    private static final String SUBJECT = "staff-123";

    private final InMemoryAccountRepository accounts = new InMemoryAccountRepository();
    private final InMemoryCommandReceiptRepository receipts = new InMemoryCommandReceiptRepository();
    private final RecordingOutbox outbox = new RecordingOutbox();

    private LinkInstitutionalUserService service;

    @BeforeEach
    void setUp() {
        service = new LinkInstitutionalUserService(accounts, receipts, outbox, FIXED_CLOCK);
    }

    // ---- key shape: scope + operation + commandId ----

    @Test
    void keyIsScopeKeyOperationAndCommandId() {
        UUID commandId = UUID.randomUUID();

        service.link(ISSUER, SUBJECT, commandId);

        var expectedKey = new IdempotencyKey(
                LinkInstitutionalUserService.IDEMPOTENCY_SCOPE_KEY,
                LinkInstitutionalUserService.IDEMPOTENCY_OPERATION_LINK_INSTITUTIONAL_USER,
                commandId);
        // service queries the receipt store with the full key before doing work
        assertThat(receipts.queriedKeys).contains(expectedKey);
        // ... and records the receipt under the same key
        assertThat(receipts.results).containsKey(expectedKey);
        // key components are non-null/non-blank per IdempotencyKey contract
        assertThat(expectedKey.scopeKey()).isNotBlank();
        assertThat(expectedKey.operation()).isNotBlank();
        assertThat(expectedKey.commandId()).isEqualTo(commandId);
    }

    // ---- same key + same SHA-256 request digest -> original result, no duplicates ----

    @Test
    void sameKeyAndSameRequestDigestReturnsOriginalResultWithoutDuplicateAccountOrOutbox() {
        UUID commandId = UUID.randomUUID();

        UUID first = service.link(ISSUER, SUBJECT, commandId);
        int accountsAfterFirst = accounts.saved.size();
        int outboxAfterFirst = outbox.events.size();
        int receiptsAfterFirst = receipts.results.size();

        UUID replayed = service.link(ISSUER, SUBJECT, commandId);

        // original result returned
        assertThat(replayed).isEqualTo(first);
        // no duplicate account
        assertThat(accounts.saved).hasSize(accountsAfterFirst);
        assertThat(accounts.saved).hasSize(1);
        // no duplicate outbox event
        assertThat(outbox.events).hasSize(outboxAfterFirst);
        assertThat(outbox.events).hasSize(1);
        // no duplicate idempotency record
        assertThat(receipts.results).hasSize(receiptsAfterFirst);
        assertThat(receipts.results).hasSize(1);
        // replay performs no new writes
        assertThat(accounts.saveAttempts).isEqualTo(1);
        assertThat(receipts.recordCalls).isEqualTo(1);
    }

    @Test
    void replayedRequestShortCircuitsBeforeAnyNewWorkOrValidation() {
        UUID commandId = UUID.randomUUID();
        UUID first = service.link(ISSUER, SUBJECT, commandId);
        int accountsAfterFirst = accounts.saved.size();
        int outboxAfterFirst = outbox.events.size();

        // identical replay: receipt checked before existsByOidcIdentity / save / append / record
        UUID replayed = service.link(ISSUER, SUBJECT, commandId);

        assertThat(replayed).isEqualTo(first);
        assertThat(accounts.saved).hasSize(accountsAfterFirst);
        assertThat(outbox.events).hasSize(outboxAfterFirst);
    }

    // ---- same key + different digest -> conflict ----

    @Test
    void sameKeyAndDifferentDigestConflicts() {
        UUID commandId = UUID.randomUUID();
        UUID first = service.link(ISSUER, SUBJECT, commandId);
        String originalDigest = receipts.results.values().iterator().next().requestDigestSha256();
        int accountsAfterFirst = accounts.saved.size();
        int outboxAfterFirst = outbox.events.size();
        int receiptsAfterFirst = receipts.results.size();

        // same key (scope + operation + commandId), different request -> different SHA-256 digest
        assertThat(sha256Hex(canonicalRequest(ISSUER, "different-subject")))
                .isNotEqualTo(originalDigest); // confirms digests differ
        assertThatThrownBy(() -> service.link(ISSUER, "different-subject", commandId))
                .isInstanceOf(IdempotencyConflictException.class);

        // original result is preserved; no side effects of the conflicting call
        assertThat(accounts.saved).hasSize(accountsAfterFirst);
        assertThat(outbox.events).hasSize(outboxAfterFirst);
        assertThat(receipts.results).hasSize(receiptsAfterFirst);
        assertThat(receipts.results.values().iterator().next().resourceRef()).isEqualTo(first);
        assertThat(receipts.results.values().iterator().next().requestDigestSha256()).isEqualTo(originalDigest);
    }

    @Test
    void conflictingCallIsNotRetried() {
        UUID commandId = UUID.randomUUID();
        service.link(ISSUER, SUBJECT, commandId);
        int findCallsAfterFirst = receipts.findCalls;
        int saveAttemptsAfterFirst = accounts.saveAttempts;
        int recordCallsAfterFirst = receipts.recordCalls;

        assertThatThrownBy(() -> service.link(ISSUER, "different-subject", commandId))
                .isInstanceOf(IdempotencyConflictException.class);

        // no blind retry: receipt re-read exactly once for the conflicting call, no writes retried
        assertThat(receipts.findCalls).isEqualTo(findCallsAfterFirst + 1);
        assertThat(accounts.saveAttempts).isEqualTo(saveAttemptsAfterFirst);
        assertThat(receipts.recordCalls).isEqualTo(recordCallsAfterFirst);
    }

    // ---- SHA-256 request digest ----

    @Test
    void requestDigestIsLowercaseHexSha256OfCanonicalRequest() {
        UUID commandId = UUID.randomUUID();

        service.link(ISSUER, SUBJECT, commandId);

        var receipt = receipts.results.values().iterator().next();
        String digest = receipt.requestDigestSha256();
        assertThat(digest).matches("[0-9a-f]{64}"); // char(64) SHA-256 hex
        assertThat(digest).isEqualTo(sha256Hex(canonicalRequest(ISSUER, SUBJECT)));
    }

    @Test
    void requestDigestIsDeterministicForSameRequestAndDiffersForDifferentRequest() {
        // digest is a pure function of the canonical request (no clock, no randomness, no commandId)
        assertThat(sha256Hex(canonicalRequest(ISSUER, SUBJECT)))
                .isEqualTo(sha256Hex(canonicalRequest(ISSUER, SUBJECT)));
        assertThat(sha256Hex(canonicalRequest(ISSUER, SUBJECT)))
                .isNotEqualTo(sha256Hex(canonicalRequest(ISSUER, "different-subject")));
        assertThat(sha256Hex(canonicalRequest(ISSUER, SUBJECT)))
                .isNotEqualTo(sha256Hex(canonicalRequest("https://other-issuer.example/oidc", SUBJECT)));

        // service-stored digest equals SHA-256 of the canonical request; commandId only affects the key, not the digest
        UUID commandId = UUID.randomUUID();
        service.link(ISSUER, SUBJECT, commandId);
        var receipt = receipts.results.values().iterator().next();
        assertThat(receipt.requestDigestSha256()).isEqualTo(sha256Hex(canonicalRequest(ISSUER, SUBJECT)));
        assertThat(receipt.key().commandId()).isEqualTo(commandId);
    }

    // ---- no blind retry on optimistic concurrency ----

    @Test
    void optimisticConcurrencyConflictIsSurfacedWithoutBlindRetry() {
        accounts.failSaveWithConflict = true;
        UUID commandId = UUID.randomUUID();

        assertThatThrownBy(() -> service.link(ISSUER, SUBJECT, commandId))
                .isInstanceOf(OptimisticConcurrencyException.class);

        // exactly one save attempt; no automatic retry with reloaded state; nothing downstream ran
        assertThat(accounts.saveAttempts).isEqualTo(1);
        assertThat(outbox.events).isEmpty();
        assertThat(receipts.results).isEmpty();
    }

    // ---- helpers ----

    /** Canonical request encoding for LinkInstitutionalUser digest. */
    static String canonicalRequest(String issuer, String staffSubject) {
        return issuer + "\n" + staffSubject;
    }

    static String sha256Hex(String canonicalRequest) {
        try {
            byte[] hash = MessageDigest.getInstance("SHA-256")
                    .digest(canonicalRequest.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(hash);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 unavailable", e);
        }
    }

    // ---- test doubles (no AWS, no DB) ----

    private record SavedAccount(IdentityAccount account, long expectedVersion) {}

    private static final class InMemoryAccountRepository implements IdentityAccountRepository {
        final List<SavedAccount> saved = new ArrayList<>();
        final Set<OidcIdentity> existingIdentities = new HashSet<>();
        int saveAttempts;
        boolean failSaveWithConflict;

        @Override
        public Optional<IdentityAccount> findById(UUID accountId) {
            return saved.stream().map(SavedAccount::account).filter(a -> a.id().equals(accountId)).findFirst();
        }

        @Override
        public boolean existsByOidcIdentity(OidcIdentity identity) {
            return existingIdentities.contains(identity)
                    || saved.stream().anyMatch(s -> s.account().oidcIdentity().equals(identity));
        }

        @Override
        public void save(IdentityAccount account, long expectedVersion) {
            saveAttempts++;
            if (failSaveWithConflict) {
                throw new OptimisticConcurrencyException(
                        "expected row_version " + expectedVersion + " but row was concurrently modified");
            }
            saved.add(new SavedAccount(account, expectedVersion));
        }
    }

    private static final class InMemoryCommandReceiptRepository implements CommandReceiptRepository {
        final Map<IdempotencyKey, CommandReceipt> results = new HashMap<>();
        final List<IdempotencyKey> queriedKeys = new ArrayList<>();
        int findCalls;
        int recordCalls;

        @Override
        public Optional<CommandReceipt> findReceipt(IdempotencyKey key) {
            findCalls++;
            queriedKeys.add(key);
            return Optional.ofNullable(results.get(key));
        }

        @Override
        public void record(IdempotencyKey key, String requestDigestSha256, UUID resourceRef) {
            recordCalls++;
            results.put(key, new CommandReceipt(key, requestDigestSha256, resourceRef));
        }
    }

    private record RecordedEvent(
            UUID eventId,
            String eventType,
            int schemaVersion,
            UUID aggregateRef,
            long aggregateVersion,
            Instant occurredAt,
            Map<String, String> payload) {}

    private static final class RecordingOutbox implements IdentityEventOutbox {
        final List<RecordedEvent> events = new ArrayList<>();

        @Override
        public void append(
                UUID eventId,
                String eventType,
                int schemaVersion,
                UUID aggregateRef,
                long aggregateVersion,
                Instant occurredAt,
                Map<String, String> payload) {
            events.add(new RecordedEvent(
                    eventId, eventType, schemaVersion, aggregateRef, aggregateVersion, occurredAt, Map.copyOf(payload)));
        }
    }
}
