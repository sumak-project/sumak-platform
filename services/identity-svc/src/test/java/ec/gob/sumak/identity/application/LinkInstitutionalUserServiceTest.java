package ec.gob.sumak.identity.application;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatNullPointerException;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import ec.gob.sumak.identity.application.port.CommandReceiptRepository;
import ec.gob.sumak.identity.application.port.IdentityAccountRepository;
import ec.gob.sumak.identity.application.port.IdentityEventOutbox;
import ec.gob.sumak.identity.domain.AccountStatus;
import ec.gob.sumak.identity.domain.IdentityAccount;
import ec.gob.sumak.identity.domain.IdentityChannel;
import ec.gob.sumak.identity.domain.OidcIdentity;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class LinkInstitutionalUserServiceTest {

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

    @Test
    void rejectsNullCollaborators() {
        assertThatNullPointerException().isThrownBy(() -> new LinkInstitutionalUserService(null, receipts, outbox, FIXED_CLOCK));
        assertThatNullPointerException().isThrownBy(() -> new LinkInstitutionalUserService(accounts, null, outbox, FIXED_CLOCK));
        assertThatNullPointerException().isThrownBy(() -> new LinkInstitutionalUserService(accounts, receipts, null, FIXED_CLOCK));
        assertThatNullPointerException().isThrownBy(() -> new LinkInstitutionalUserService(accounts, receipts, outbox, null));
    }

    @Test
    void linkCreatesPendingStaffAccountSavesWithExpectedVersionMinusOneAppendsOutboxAndRecordsReceipt() {
        UUID commandId = UUID.randomUUID();

        UUID accountId = service.link(ISSUER, SUBJECT, commandId);

        assertThat(accountId).isNotNull();

        // account saved once as insert with expectedVersion -1
        assertThat(accounts.saved).hasSize(1);
        var saved = accounts.saved.get(0);
        assertThat(saved.account().id()).isEqualTo(accountId);
        assertThat(saved.expectedVersion()).isEqualTo(-1);
        assertThat(saved.account().status()).isEqualTo(AccountStatus.PENDING);
        assertThat(saved.account().channel()).isEqualTo(IdentityChannel.STAFF);
        assertThat(saved.account().version()).isZero();
        assertThat(saved.account().oidcIdentity()).isEqualTo(new OidcIdentity(ISSUER, SUBJECT));

        // outbox event IdentityLinked v1
        assertThat(outbox.events).hasSize(1);
        var event = outbox.events.get(0);
        assertThat(event.eventType()).isEqualTo("IdentityLinked");
        assertThat(event.schemaVersion()).isEqualTo(1);
        assertThat(event.aggregateRef()).isEqualTo(accountId);
        assertThat(event.aggregateVersion()).isZero();
        assertThat(event.occurredAt()).isEqualTo(FIXED_NOW);
        assertThat(event.eventId()).isNotNull();
        assertThat(event.payload())
                .containsEntry("accountRef", accountId.toString())
                .containsEntry("channel", "STAFF")
                .containsEntry("status", "PENDING")
                .containsEntry("version", "0")
                .hasSize(4);

        // idempotency receipt recorded
        assertThat(receipts.results).containsEntry(commandId, accountId);
    }

    // ---- idempotency ----

    @Test
    void replayedCommandReturnsPreviousResultWithoutDuplicatingWork() {
        UUID commandId = UUID.randomUUID();
        UUID first = service.link(ISSUER, SUBJECT, commandId);

        UUID replayed = service.link(ISSUER, SUBJECT, commandId);

        assertThat(replayed).isEqualTo(first);
        assertThat(accounts.saved).hasSize(1);
        assertThat(outbox.events).hasSize(1);
        assertThat(receipts.results).hasSize(1);
    }

    @Test
    void preExistingReceiptShortCircuitsBeforeAnyValidationOrWork() {
        UUID commandId = UUID.randomUUID();
        UUID previous = UUID.randomUUID();
        receipts.results.put(commandId, previous);

        UUID result = service.link("", "", commandId); // even invalid input is skipped on replay

        assertThat(result).isEqualTo(previous);
        assertThat(accounts.saved).isEmpty();
        assertThat(outbox.events).isEmpty();
    }

    @Test
    void nullCommandIdRejected() {
        assertThatNullPointerException().isThrownBy(() -> service.link(ISSUER, SUBJECT, null));
    }

    // ---- negative cases ----

    @Test
    void alreadyLinkedIdentityRejectedWithoutSideEffects() {
        accounts.existingIdentities.add(new OidcIdentity(ISSUER, SUBJECT));

        assertThatThrownBy(() -> service.link(ISSUER, SUBJECT, UUID.randomUUID()))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("already linked");

        assertThat(accounts.saved).isEmpty();
        assertThat(outbox.events).isEmpty();
        assertThat(receipts.results).isEmpty();
    }

    @Test
    void invalidIdentityRejectedWithoutSideEffects() {
        assertThatThrownBy(() -> service.link(" ", SUBJECT, UUID.randomUUID()))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> service.link(ISSUER, "", UUID.randomUUID()))
                .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> service.link(null, SUBJECT, UUID.randomUUID()))
                .isInstanceOf(NullPointerException.class);

        assertThat(accounts.saved).isEmpty();
        assertThat(outbox.events).isEmpty();
        assertThat(receipts.results).isEmpty();
    }

    // ---- test doubles (no AWS, no DB) ----

    private record SavedAccount(IdentityAccount account, long expectedVersion) {}

    private static final class InMemoryAccountRepository implements IdentityAccountRepository {
        final List<SavedAccount> saved = new ArrayList<>();
        final List<OidcIdentity> existingIdentities = new ArrayList<>();

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
            saved.add(new SavedAccount(account, expectedVersion));
        }
    }

    private static final class InMemoryCommandReceiptRepository implements CommandReceiptRepository {
        final Map<UUID, UUID> results = new HashMap<>();

        @Override
        public Optional<UUID> resultFor(UUID commandId) {
            return Optional.ofNullable(results.get(commandId));
        }

        @Override
        public void record(UUID commandId, UUID accountId) {
            results.put(commandId, accountId);
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
            events.add(new RecordedEvent(eventId, eventType, schemaVersion, aggregateRef, aggregateVersion, occurredAt, Map.copyOf(payload)));
        }
    }
}
