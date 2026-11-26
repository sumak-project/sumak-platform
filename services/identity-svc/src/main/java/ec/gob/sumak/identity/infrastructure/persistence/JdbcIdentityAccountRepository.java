package ec.gob.sumak.identity.infrastructure.persistence;

import ec.gob.sumak.identity.application.port.IdentityAccountRepository;
import ec.gob.sumak.identity.application.port.OptimisticConcurrencyException;
import ec.gob.sumak.identity.domain.AccountStatus;
import ec.gob.sumak.identity.domain.IdentityAccount;
import ec.gob.sumak.identity.domain.IdentityChannel;
import ec.gob.sumak.identity.domain.OidcIdentity;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;

public final class JdbcIdentityAccountRepository implements IdentityAccountRepository {
    private static final String FIND = """
            SELECT id, issuer, subject, channel, status, row_version
            FROM identity_account
            WHERE id = ?
            """;
    private static final String EXISTS = """
            SELECT 1 FROM identity_account WHERE issuer = ? AND subject = ?
            """;
    private static final String INSERT = """
            INSERT INTO identity_account (
                id, issuer, subject, channel, status, row_version
            ) VALUES (?, ?, ?, ?, ?, ?)
            """;
    private static final String UPDATE = """
            UPDATE identity_account
            SET issuer = ?,
                subject = ?,
                channel = ?,
                status = ?,
                row_version = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND row_version = ?
            """;

    private final JdbcIdentityTransaction transactions;

    public JdbcIdentityAccountRepository(JdbcIdentityTransaction transactions) {
        this.transactions = Objects.requireNonNull(transactions, "transactions");
    }

    @Override
    public Optional<IdentityAccount> findById(UUID accountId) {
        try (var statement = transactions.connection().prepareStatement(FIND)) {
            statement.setObject(1, Objects.requireNonNull(accountId, "accountId"));
            try (var result = statement.executeQuery()) {
                return result.next() ? Optional.of(toAccount(result)) : Optional.empty();
            }
        } catch (SQLException failure) {
            throw persistenceFailure("read identity account", failure);
        }
    }

    @Override
    public boolean existsByOidcIdentity(OidcIdentity identity) {
        Objects.requireNonNull(identity, "identity");
        try (var statement = transactions.connection().prepareStatement(EXISTS)) {
            statement.setString(1, identity.issuer());
            statement.setString(2, identity.subject());
            try (var result = statement.executeQuery()) {
                return result.next();
            }
        } catch (SQLException failure) {
            throw persistenceFailure("check OIDC identity", failure);
        }
    }

    @Override
    public void save(IdentityAccount account, long expectedVersion) {
        Objects.requireNonNull(account, "account");
        if (expectedVersion == -1) {
            insert(account);
            return;
        }
        if (expectedVersion < 0 || account.version() != expectedVersion + 1) {
            throw new IllegalArgumentException("updated account version must immediately follow expectedVersion");
        }
        update(account, expectedVersion);
    }

    private void insert(IdentityAccount account) {
        if (account.version() != 0) {
            throw new IllegalArgumentException("new identity account must start at version 0");
        }
        try (var statement = transactions.connection().prepareStatement(INSERT)) {
            statement.setObject(1, account.id());
            statement.setString(2, account.oidcIdentity().issuer());
            statement.setString(3, account.oidcIdentity().subject());
            statement.setString(4, account.channel().name());
            statement.setString(5, account.status().name());
            statement.setLong(6, account.version());
            statement.executeUpdate();
        } catch (SQLException failure) {
            throw persistenceFailure("insert identity account", failure);
        }
    }

    private void update(IdentityAccount account, long expectedVersion) {
        try (var statement = transactions.connection().prepareStatement(UPDATE)) {
            statement.setString(1, account.oidcIdentity().issuer());
            statement.setString(2, account.oidcIdentity().subject());
            statement.setString(3, account.channel().name());
            statement.setString(4, account.status().name());
            statement.setLong(5, account.version());
            statement.setObject(6, account.id());
            statement.setLong(7, expectedVersion);
            if (statement.executeUpdate() != 1) {
                throw new OptimisticConcurrencyException(account.id(), expectedVersion);
            }
        } catch (SQLException failure) {
            throw persistenceFailure("update identity account", failure);
        }
    }

    private static IdentityAccount toAccount(ResultSet result) throws SQLException {
        return IdentityAccount.restore(
                result.getObject("id", UUID.class),
                new OidcIdentity(result.getString("issuer"), result.getString("subject")),
                IdentityChannel.valueOf(result.getString("channel")),
                AccountStatus.valueOf(result.getString("status")),
                result.getLong("row_version"),
                List.of());
    }

    private static IllegalStateException persistenceFailure(String operation, SQLException failure) {
        return new IllegalStateException("failed to " + operation, failure);
    }
}
