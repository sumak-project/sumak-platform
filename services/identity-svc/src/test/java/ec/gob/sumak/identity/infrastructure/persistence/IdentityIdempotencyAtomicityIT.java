package ec.gob.sumak.identity.infrastructure.persistence;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import ec.gob.sumak.identity.application.LinkInstitutionalUserCommand;
import ec.gob.sumak.identity.application.LinkInstitutionalUserService;
import ec.gob.sumak.identity.application.port.IdentityEventOutbox;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.SQLFeatureNotSupportedException;
import java.sql.Statement;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.UUID;
import java.util.logging.Logger;
import javax.sql.DataSource;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@Testcontainers
class IdentityIdempotencyAtomicityIT {
    @Container
    static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine");

    private static DataSource dataSource;

    @BeforeAll
    static void migrate() {
        dataSource = new DriverManagerDataSource(
                POSTGRES.getJdbcUrl(), POSTGRES.getUsername(), POSTGRES.getPassword());
        Flyway flyway = Flyway.configure()
                .dataSource(dataSource)
                .locations("classpath:db/migration")
                .cleanDisabled(false)
                .load();
        flyway.clean();
        assertThat(flyway.migrate().success).isTrue();
    }

    @BeforeEach
    void cleanTables() throws SQLException {
        try (Connection connection = dataSource.getConnection(); Statement statement = connection.createStatement()) {
            statement.execute("TRUNCATE TABLE idempotency_record, outbox_event, identity_account CASCADE");
        }
    }

    @Test
    void accountOutboxAndReceiptCommitTogetherAndReplayHasNoDuplicateEffect() throws SQLException {
        LinkInstitutionalUserService service = serviceWith(null);
        UUID commandId = UUID.randomUUID();
        var command = new LinkInstitutionalUserCommand(
                "admin:synthetic", "https://issuer.example", "staff-1", commandId);

        UUID first = service.link(command);
        UUID replay = service.link(command);

        assertThat(replay).isEqualTo(first);
        assertThat(count("identity_account")).isEqualTo(1);
        assertThat(count("outbox_event")).isEqualTo(1);
        assertThat(count("idempotency_record")).isEqualTo(1);
        try (Connection connection = dataSource.getConnection();
                var statement = connection.prepareStatement("""
                        SELECT scope_key, operation, request_digest, status, resource_ref
                        FROM idempotency_record
                        WHERE command_id = ?
                        """)) {
            statement.setObject(1, commandId);
            try (var result = statement.executeQuery()) {
                assertThat(result.next()).isTrue();
                assertThat(result.getString("scope_key")).isEqualTo("admin:synthetic");
                assertThat(result.getString("operation")).isEqualTo("LinkInstitutionalUser");
                assertThat(result.getString("request_digest")).matches("[0-9a-f]{64}");
                assertThat(result.getString("status")).isEqualTo("COMPLETED");
                assertThat(result.getObject("resource_ref", UUID.class)).isEqualTo(first);
            }
        }
    }

    @Test
    void sameKeyWithDifferentDigestConflictsWithoutNewEffect() throws SQLException {
        LinkInstitutionalUserService service = serviceWith(null);
        UUID commandId = UUID.randomUUID();
        service.link(new LinkInstitutionalUserCommand(
                "admin:synthetic", "https://issuer.example", "staff-1", commandId));

        assertThatThrownBy(() -> service.link(new LinkInstitutionalUserCommand(
                        "admin:synthetic", "https://issuer.example", "staff-2", commandId)))
                .isInstanceOf(ec.gob.sumak.identity.application.port.IdempotencyConflictException.class);

        assertThat(count("identity_account")).isEqualTo(1);
        assertThat(count("outbox_event")).isEqualTo(1);
        assertThat(count("idempotency_record")).isEqualTo(1);
    }

    @Test
    void downstreamFailureRollsBackAccountOutboxAndPendingReceipt() throws SQLException {
        IdentityEventOutbox failure = (eventId, eventType, schemaVersion, aggregateRef, aggregateVersion,
                occurredAt, payload) -> {
            throw new IllegalStateException("synthetic outbox failure");
        };
        LinkInstitutionalUserService service = serviceWith(failure);

        assertThatThrownBy(() -> service.link(new LinkInstitutionalUserCommand(
                        "admin:synthetic", "https://issuer.example", "staff-rollback", UUID.randomUUID())))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("synthetic outbox failure");

        assertThat(count("identity_account")).isZero();
        assertThat(count("outbox_event")).isZero();
        assertThat(count("idempotency_record")).isZero();
    }

    private static LinkInstitutionalUserService serviceWith(IdentityEventOutbox outboxOverride) {
        var transaction = new JdbcIdentityTransaction(dataSource);
        IdentityEventOutbox outbox = outboxOverride == null
                ? new JdbcIdentityEventOutbox(transaction)
                : outboxOverride;
        return new LinkInstitutionalUserService(
                new JdbcIdentityAccountRepository(transaction),
                new JdbcCommandReceiptRepository(transaction),
                outbox,
                transaction,
                Clock.fixed(Instant.parse("2026-11-26T12:00:00Z"), ZoneOffset.UTC));
    }

    private static long count(String table) throws SQLException {
        try (Connection connection = dataSource.getConnection(); Statement statement = connection.createStatement()) {
            try (var result = statement.executeQuery("SELECT count(*) FROM " + table)) {
                result.next();
                return result.getLong(1);
            }
        }
    }

    private record DriverManagerDataSource(String url, String username, String password) implements DataSource {
        @Override
        public Connection getConnection() throws SQLException {
            return DriverManager.getConnection(url, username, password);
        }

        @Override
        public Connection getConnection(String user, String pass) throws SQLException {
            return DriverManager.getConnection(url, user, pass);
        }

        @Override
        public PrintWriter getLogWriter() {
            return null;
        }

        @Override
        public void setLogWriter(PrintWriter out) {}

        @Override
        public void setLoginTimeout(int seconds) {}

        @Override
        public int getLoginTimeout() {
            return 0;
        }

        @Override
        public Logger getParentLogger() throws SQLFeatureNotSupportedException {
            throw new SQLFeatureNotSupportedException();
        }

        @Override
        public <T> T unwrap(Class<T> iface) throws SQLException {
            throw new SQLException("not a wrapper");
        }

        @Override
        public boolean isWrapperFor(Class<?> iface) {
            return false;
        }
    }
}
