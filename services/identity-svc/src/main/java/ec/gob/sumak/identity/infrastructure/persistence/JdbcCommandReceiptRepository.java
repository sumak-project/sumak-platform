package ec.gob.sumak.identity.infrastructure.persistence;

import ec.gob.sumak.identity.application.CommandClaim;
import ec.gob.sumak.identity.application.CommandKey;
import ec.gob.sumak.identity.application.port.CommandReceiptRepository;
import ec.gob.sumak.identity.application.port.IdempotencyConflictException;
import java.sql.SQLException;
import java.util.Objects;
import java.util.UUID;

public final class JdbcCommandReceiptRepository implements CommandReceiptRepository {
    private static final String INSERT_CLAIM = """
            INSERT INTO idempotency_record (
                scope_key, operation, command_id, request_digest, status, created_at
            ) VALUES (?, ?, ?, ?, 'PENDING', CURRENT_TIMESTAMP)
            ON CONFLICT (scope_key, operation, command_id) DO NOTHING
            """;
    private static final String SELECT_CLAIM = """
            SELECT request_digest, status, resource_ref
            FROM idempotency_record
            WHERE scope_key = ? AND operation = ? AND command_id = ?
            FOR UPDATE
            """;
    private static final String COMPLETE = """
            UPDATE idempotency_record
            SET status = 'COMPLETED',
                resource_ref = ?,
                account_id = ?,
                result = jsonb_build_object('resourceRef', ?::text)
            WHERE scope_key = ?
              AND operation = ?
              AND command_id = ?
              AND request_digest = ?
              AND status = 'PENDING'
            """;

    private final JdbcIdentityTransaction transactions;

    public JdbcCommandReceiptRepository(JdbcIdentityTransaction transactions) {
        this.transactions = Objects.requireNonNull(transactions, "transactions");
    }

    @Override
    public CommandClaim claim(CommandKey key, String requestDigest) {
        requireDigest(requestDigest);
        try (var statement = transactions.connection().prepareStatement(INSERT_CLAIM)) {
            setKey(statement, key);
            statement.setString(4, requestDigest);
            if (statement.executeUpdate() == 1) {
                return new CommandClaim.Acquired();
            }
        } catch (SQLException failure) {
            throw persistenceFailure("claim idempotency command", failure);
        }

        try (var statement = transactions.connection().prepareStatement(SELECT_CLAIM)) {
            setKey(statement, key);
            try (var result = statement.executeQuery()) {
                if (!result.next()) {
                    throw new IllegalStateException("idempotency claim disappeared");
                }
                String storedDigest = result.getString("request_digest");
                if (!storedDigest.equals(requestDigest)) {
                    throw new IdempotencyConflictException(
                            "command key was already used with a different request digest");
                }
                String status = result.getString("status");
                UUID resourceRef = result.getObject("resource_ref", UUID.class);
                if ("COMPLETED".equals(status) && resourceRef != null) {
                    return new CommandClaim.Completed(resourceRef);
                }
                throw new IdempotencyConflictException("command is already in progress");
            }
        } catch (SQLException failure) {
            throw persistenceFailure("read idempotency command", failure);
        }
    }

    @Override
    public void complete(CommandKey key, String requestDigest, UUID resourceRef) {
        requireDigest(requestDigest);
        Objects.requireNonNull(resourceRef, "resourceRef");
        try (var statement = transactions.connection().prepareStatement(COMPLETE)) {
            statement.setObject(1, resourceRef);
            statement.setObject(2, resourceRef);
            statement.setObject(3, resourceRef);
            statement.setString(4, key.scopeKey());
            statement.setString(5, key.operation());
            statement.setObject(6, key.commandId());
            statement.setString(7, requestDigest);
            if (statement.executeUpdate() != 1) {
                throw new IdempotencyConflictException("idempotency command cannot be completed");
            }
        } catch (SQLException failure) {
            throw persistenceFailure("complete idempotency command", failure);
        }
    }

    private static void setKey(java.sql.PreparedStatement statement, CommandKey key) throws SQLException {
        Objects.requireNonNull(key, "key");
        statement.setString(1, key.scopeKey());
        statement.setString(2, key.operation());
        statement.setObject(3, key.commandId());
    }

    private static void requireDigest(String requestDigest) {
        if (Objects.requireNonNull(requestDigest, "requestDigest").length() != 64) {
            throw new IllegalArgumentException("requestDigest must be a SHA-256 hex digest");
        }
    }

    private static IllegalStateException persistenceFailure(String operation, SQLException failure) {
        return new IllegalStateException("failed to " + operation, failure);
    }
}
