package ec.gob.sumak.identity.application;

import ec.gob.sumak.identity.application.port.CommandReceiptRepository;
import ec.gob.sumak.identity.application.port.IdentityAccountRepository;
import ec.gob.sumak.identity.application.port.IdentityEventOutbox;
import ec.gob.sumak.identity.domain.IdentityAccount;
import ec.gob.sumak.identity.domain.OidcIdentity;
import java.time.Clock;
import java.time.Instant;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

public final class LinkInstitutionalUserService {
    private final IdentityAccountRepository accounts;
    private final CommandReceiptRepository receipts;
    private final IdentityEventOutbox outbox;
    private final Clock clock;

    public LinkInstitutionalUserService(
            IdentityAccountRepository accounts,
            CommandReceiptRepository receipts,
            IdentityEventOutbox outbox,
            Clock clock) {
        this.accounts = Objects.requireNonNull(accounts, "accounts");
        this.receipts = Objects.requireNonNull(receipts, "receipts");
        this.outbox = Objects.requireNonNull(outbox, "outbox");
        this.clock = Objects.requireNonNull(clock, "clock");
    }

    public UUID link(String issuer, String staffSubject, UUID commandId) {
        Objects.requireNonNull(commandId, "commandId");
        var previousResult = receipts.resultFor(commandId);
        if (previousResult.isPresent()) {
            return previousResult.get();
        }

        var identity = new OidcIdentity(issuer, staffSubject);
        if (accounts.existsByOidcIdentity(identity)) {
            throw new IllegalStateException("identity is already linked");
        }

        var account = IdentityAccount.linkInstitutional(UUID.randomUUID(), identity);
        accounts.save(account, -1);
        Instant occurredAt = clock.instant();
        outbox.append(
                UUID.randomUUID(),
                "IdentityLinked",
                1,
                account.id(),
                account.version(),
                occurredAt,
                Map.of(
                        "accountRef", account.id().toString(),
                        "channel", account.channel().name(),
                        "status", account.status().name(),
                        "version", Long.toString(account.version())));
        receipts.record(commandId, account.id());
        return account.id();
    }
}
