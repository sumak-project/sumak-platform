package ec.gob.sumak.identity.application;

import ec.gob.sumak.identity.application.port.CommandReceiptRepository;
import ec.gob.sumak.identity.application.port.IdentityAccountRepository;
import ec.gob.sumak.identity.application.port.IdentityEventOutbox;
import ec.gob.sumak.identity.application.port.IdentityTransaction;
import ec.gob.sumak.identity.domain.IdentityAccount;
import ec.gob.sumak.identity.domain.OidcIdentity;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Clock;
import java.time.Instant;
import java.util.HexFormat;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.function.Supplier;

public final class LinkInstitutionalUserService {
    public static final String IDEMPOTENCY_SCOPE_KEY = "identity-svc";
    public static final String IDEMPOTENCY_OPERATION_LINK_INSTITUTIONAL_USER = "LinkInstitutionalUser";

    private final IdentityAccountRepository accounts;
    private final CommandReceiptRepository receipts;
    private final IdentityEventOutbox outbox;
    private final IdentityTransaction transactions;
    private final Clock clock;

    public LinkInstitutionalUserService(
            IdentityAccountRepository accounts,
            CommandReceiptRepository receipts,
            IdentityEventOutbox outbox,
            IdentityTransaction transactions,
            Clock clock) {
        this.accounts = Objects.requireNonNull(accounts, "accounts");
        this.receipts = Objects.requireNonNull(receipts, "receipts");
        this.outbox = Objects.requireNonNull(outbox, "outbox");
        this.transactions = Objects.requireNonNull(transactions, "transactions");
        this.clock = Objects.requireNonNull(clock, "clock");
    }

    public LinkInstitutionalUserService(
            IdentityAccountRepository accounts,
            CommandReceiptRepository receipts,
            IdentityEventOutbox outbox,
            Clock clock) {
        this(accounts, receipts, outbox, new IdentityTransaction() {
            @Override
            public <T> T required(Supplier<T> work) {
                return work.get();
            }
        }, clock);
    }

    public UUID link(String issuer, String staffSubject, UUID commandId) {
        Objects.requireNonNull(commandId, "commandId");
        var legacyResult = receipts.resultFor(commandId);
        if (legacyResult.isPresent()) {
            return legacyResult.get();
        }
        return link(new LinkInstitutionalUserCommand(
                IDEMPOTENCY_SCOPE_KEY, issuer, staffSubject, commandId));
    }

    public UUID link(LinkInstitutionalUserCommand command) {
        Objects.requireNonNull(command, "command");
        var identity = new OidcIdentity(command.issuer(), command.staffSubject());
        var key = new CommandKey(
                command.scopeKey(), IDEMPOTENCY_OPERATION_LINK_INSTITUTIONAL_USER, command.commandId());
        var digest = requestDigest(identity);
        return transactions.required(() -> linkAtomically(identity, key, digest));
    }

    private UUID linkAtomically(OidcIdentity identity, CommandKey key, String digest) {
        var claim = receipts.claim(key, digest);
        if (claim instanceof CommandClaim.Completed completed) {
            return completed.resourceRef();
        }
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
        receipts.complete(key, digest, account.id());
        return account.id();
    }

    private static String requestDigest(OidcIdentity identity) {
        try {
            var digest = MessageDigest.getInstance("SHA-256");
            digest.update(identity.issuer().getBytes(StandardCharsets.UTF_8));
            digest.update((byte) '\n');
            digest.update(identity.subject().getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest.digest());
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is unavailable", exception);
        }
    }
}
