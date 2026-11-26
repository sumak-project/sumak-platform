package ec.gob.sumak.identity.infrastructure.persistence;

import ec.gob.sumak.identity.application.port.IdentityTransaction;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.Objects;
import java.util.function.Supplier;
import javax.sql.DataSource;

public final class JdbcIdentityTransaction implements IdentityTransaction {
    private final DataSource dataSource;
    private final ThreadLocal<Connection> currentConnection = new ThreadLocal<>();

    public JdbcIdentityTransaction(DataSource dataSource) {
        this.dataSource = Objects.requireNonNull(dataSource, "dataSource");
    }

    @Override
    public <T> T required(Supplier<T> work) {
        Objects.requireNonNull(work, "work");
        if (currentConnection.get() != null) {
            return work.get();
        }

        try (Connection connection = dataSource.getConnection()) {
            connection.setAutoCommit(false);
            currentConnection.set(connection);
            try {
                T result = work.get();
                connection.commit();
                return result;
            } catch (RuntimeException | Error failure) {
                rollback(connection, failure);
                throw failure;
            } finally {
                currentConnection.remove();
            }
        } catch (SQLException failure) {
            throw new IllegalStateException("identity database transaction failed", failure);
        }
    }

    Connection connection() {
        Connection connection = currentConnection.get();
        if (connection == null) {
            throw new IllegalStateException("identity persistence operation requires an active transaction");
        }
        return connection;
    }

    private static void rollback(Connection connection, Throwable originalFailure) {
        try {
            connection.rollback();
        } catch (SQLException rollbackFailure) {
            originalFailure.addSuppressed(rollbackFailure);
        }
    }
}
