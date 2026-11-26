package ec.gob.sumak.identity.infrastructure.persistence;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.UUID;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

/**
 * Integration gate (requires Docker + a PostgreSQL image at runtime; NOT runnable in this environment).
 * Validates Flyway clean migration of the owning identity database and key invariants on real PostgreSQL.
 * No cross-owner SQL; no real personal data; synthetic data only.
 */
@Testcontainers
class IdentitySchemaMigrationIT {

    @Container
    static final PostgreSQLContainer<?> POSTGRES = new PostgreSQLContainer<>("postgres:16-alpine");

    private static String jdbcUrl;
    private static String username;
    private static String password;

    @BeforeAll
    static void migrate() {
        jdbcUrl = POSTGRES.getJdbcUrl();
        username = POSTGRES.getUsername();
        password = POSTGRES.getPassword();

        Flyway flyway = Flyway.configure()
                .dataSource(jdbcUrl, username, password)
                .locations("classpath:db/migration")
                .cleanDisabled(false)
                .load();
        flyway.clean(); // clean path
        var result = flyway.migrate(); // upgrade path from empty
        assertThat(result.success).isTrue();
        assertThat(result.migrationsExecuted).isEqualTo(2);
    }

    @Test
    void createsAllOwnedTables() throws SQLException {
        try (Connection c = connect(); Statement s = c.createStatement()) {
            for (String table : new String[] {
                "identity_account", "identity_person_link", "institutional_role", "role_assignment",
                "identity_security_event", "outbox_event", "inbox_event", "idempotency_record"}) {
                var rs = s.executeQuery("SELECT to_regclass('public." + table + "') IS NOT NULL");
                rs.next();
                assertThat(rs.getBoolean(1)).as("table %s exists", table).isTrue();
            }
        }
    }

    @Test
    void seedsAllInstitutionalRoles() throws SQLException {
        try (Connection c = connect(); Statement s = c.createStatement()) {
            var rs = s.executeQuery("SELECT count(*) FROM institutional_role");
            rs.next();
            assertThat(rs.getLong(1)).isEqualTo(5);
        }
    }

    @Test
    void uniqueIssuerSubjectIsEnforced() throws SQLException {
        UUID id1 = UUID.randomUUID();
        UUID id2 = UUID.randomUUID();
        try (Connection c = connect(); Statement s = c.createStatement()) {
            insertAccount(s, id1, "issuer-x", "synthetic-subject");
            assertThatThrownBy(() -> insertAccount(s, id2, "issuer-x", "synthetic-subject"))
                    .isInstanceOf(SQLException.class);
            // same subject under a different issuer is allowed (issuer isolation)
            insertAccount(s, id2, "issuer-y", "synthetic-subject");
        }
    }

    @Test
    void invalidStatusAndChannelRejected() throws SQLException {
        try (Connection c = connect(); Statement s = c.createStatement()) {
            assertThatThrownBy(() -> s.execute(
                    "INSERT INTO identity_account (id, issuer, subject, channel, status) VALUES ('"
                            + UUID.randomUUID() + "', 'i', 's1', 'STAFF', 'NOT_A_STATUS')"))
                    .isInstanceOf(SQLException.class);
            assertThatThrownBy(() -> s.execute(
                    "INSERT INTO identity_account (id, issuer, subject, channel, status) VALUES ('"
                            + UUID.randomUUID() + "', 'i', 's2', 'NOT_A_CHANNEL', 'PENDING')"))
                    .isInstanceOf(SQLException.class);
        }
    }

    @Test
    void outboxAndIdempotencySchemasPresent() throws SQLException {
        try (Connection c = connect(); Statement s = c.createStatement()) {
            s.execute("INSERT INTO outbox_event (id, event_type, schema_version, aggregate_ref, aggregate_version, occurred_at, payload) "
                    + "VALUES ('" + UUID.randomUUID() + "', 'IdentityLinked', 1, '" + UUID.randomUUID()
                    + "', 0, now(), '{}'::jsonb)");
            s.execute("INSERT INTO idempotency_record "
                    + "(scope_key, operation, command_id, request_digest, status) VALUES "
                    + "('synthetic', 'test', '" + UUID.randomUUID() + "', repeat('a', 64), 'PENDING')");
            assertThatThrownBy(() -> s.execute(
                    "INSERT INTO outbox_event (id, event_type, schema_version, aggregate_ref, aggregate_version, occurred_at, payload) "
                            + "VALUES ('" + UUID.randomUUID() + "', 'X', 0, '" + UUID.randomUUID() + "', 0, now(), '{}'::jsonb)"))
                    .isInstanceOf(SQLException.class); // schema_version > 0 check
        }
    }

    private static void insertAccount(Statement s, UUID id, String issuer, String subject) throws SQLException {
        s.execute("INSERT INTO identity_account (id, issuer, subject, channel, status) VALUES ('"
                + id + "', '" + issuer + "', '" + subject + "', 'STAFF', 'PENDING')");
    }

    private static Connection connect() throws SQLException {
        return DriverManager.getConnection(jdbcUrl, username, password);
    }
}
