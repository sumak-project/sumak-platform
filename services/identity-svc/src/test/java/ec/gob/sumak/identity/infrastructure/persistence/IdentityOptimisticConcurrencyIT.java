package ec.gob.sumak.identity.infrastructure.persistence;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import ec.gob.sumak.identity.application.port.OptimisticConcurrencyException;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.SQLFeatureNotSupportedException;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.logging.Logger;
import javax.sql.DataSource;
import org.flywaydb.core.Flyway;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

/**
 * SCRUM-60 — Optimistic concurrency on REAL PostgreSQL (Testcontainers {@code postgres:16-alpine} + Flyway).
 * No cross-owner SQL; synthetic data only; requires Docker at runtime.
 *
 * <p>Acceptance under test:
 * <ul>
 *   <li>PostgreSQL conditional UPDATE uses expected {@code row_version}:
 *       {@code UPDATE identity_account SET ..., row_version = row_version + 1
 *       WHERE id = ? AND row_version = ?};</li>
 *   <li>affected row count {@code 1} = success; {@code 0} = stale concurrent writer conflict
 *       (surfaced to the caller as {@code OptimisticConcurrencyException} by the port/adapter);</li>
 *   <li>stale concurrent writers conflict;</li>
 *   <li>two SIMULTANEOUS edits produce exactly one success / one conflict
 *       (READ COMMITTED default; second updater blocks on the row lock, then re-evaluates
 *       {@code WHERE row_version = ?} against the latest committed value);</li>
 *   <li>no blind retry: the loser is not re-applied; final {@code row_version} reflects
 *       exactly one applied edit; no lost update.</li>
 * </ul>
 *
 * <p>The raw-SQL assertions here pin the exact PostgreSQL semantics the
 * {@code IdentityAccountRepository.save(account, expectedVersion)} adapter must translate
 * ({@code updateCount == 0} -> {@code OptimisticConcurrencyException}); the application-level
 * "no retry" contract is unit-tested in
 * {@code ec.gob.sumak.identity.application.OptimisticConcurrencyNoBlindRetryTest}.
 */
@Testcontainers
class IdentityOptimisticConcurrencyIT {

    /** Conditional update keyed on expected row_version. */
    private static final String CONDITIONAL_UPDATE =
            "UPDATE identity_account "
                    + "SET status = ?, row_version = row_version + 1, updated_at = CURRENT_TIMESTAMP "
                    + "WHERE id = ? AND row_version = ?";

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
        flyway.clean();
        assertThat(flyway.migrate().success).isTrue();
    }

    @BeforeEach
    void cleanTables() throws SQLException {
        try (Connection c = connect(); Statement s = c.createStatement()) {
            s.execute("TRUNCATE TABLE identity_account CASCADE");
        }
    }

    // ---- single conditional update ----

    @Test
    void conditionalUpdateWithExpectedRowVersionSucceedsOnceAndIncrementsRowVersion() throws SQLException {
        UUID id = insertAccount(0L, "PENDING");

        int updated;
        try (Connection c = connect(); PreparedStatement ps = c.prepareStatement(CONDITIONAL_UPDATE)) {
            ps.setString(1, "ACTIVE");
            ps.setObject(2, id);
            ps.setLong(3, 0L); // expected row_version
            updated = ps.executeUpdate();
        }

        assertThat(updated).isEqualTo(1);
        assertThat(readRowVersion(id)).isEqualTo(1L);
        assertThat(readStatus(id)).isEqualTo("ACTIVE");
    }

    // ---- stale concurrent writer conflicts ----

    @Test
    void staleExpectedRowVersionConflictsWithZeroRowsUpdatedAndDoesNotClobber() throws SQLException {
        UUID id = insertAccount(0L, "PENDING");

        // writer 1 succeeds with expected row_version=0
        try (Connection c = connect(); PreparedStatement ps = c.prepareStatement(CONDITIONAL_UPDATE)) {
            ps.setString(1, "ACTIVE");
            ps.setObject(2, id);
            ps.setLong(3, 0L);
            assertThat(ps.executeUpdate()).isEqualTo(1);
        }

        // writer 2 is STALE: it read row_version=0 but the row is now at row_version=1
        int staleUpdated;
        try (Connection c = connect(); PreparedStatement ps = c.prepareStatement(CONDITIONAL_UPDATE)) {
            ps.setString(1, "SUSPENDED"); // stale writer tries to overwrite with different status
            ps.setObject(2, id);
            ps.setLong(3, 0L); // stale expected row_version
            staleUpdated = ps.executeUpdate();
        }

        assertThat(staleUpdated).isZero(); // conflict signal
        // no lost update: winner's effect preserved; stale writer not applied; no blind retry re-applied it
        assertThat(readRowVersion(id)).isEqualTo(1L);
        assertThat(readStatus(id)).isEqualTo("ACTIVE");
    }

    @Test
    void jdbcRepositorySurfacesStaleExpectedVersionWithoutRetrying() throws SQLException {
        UUID id = insertAccount(0L, "PENDING");
        DataSource source = new DriverManagerDataSource(jdbcUrl, username, password);
        var transaction = new JdbcIdentityTransaction(source);
        var repository = new JdbcIdentityAccountRepository(transaction);

        var winner = transaction.required(() -> repository.findById(id).orElseThrow());
        var stale = transaction.required(() -> repository.findById(id).orElseThrow());

        winner.activate();
        transaction.required(() -> {
            repository.save(winner, 0);
            return null;
        });

        stale.suspend();
        assertThatThrownBy(() -> transaction.required(() -> {
                    repository.save(stale, 0);
                    return null;
                }))
                .isInstanceOf(OptimisticConcurrencyException.class);

        assertThat(readRowVersion(id)).isEqualTo(1L);
        assertThat(readStatus(id)).isEqualTo("ACTIVE");
    }

    // ---- two SIMULTANEOUS edits: exactly one success / one conflict ----

    @Test
    void twoSimultaneousEditsProduceExactlyOneSuccessAndOneConflict() throws Exception {
        UUID id = insertAccount(0L, "PENDING");
        int workers = 2;

        // both workers read row_version BEFORE either updates...
        CountDownLatch bothRead = new CountDownLatch(workers);
        // ...and both attempt the conditional UPDATE concurrently
        CountDownLatch startUpdate = new CountDownLatch(1);

        AtomicInteger successCount = new AtomicInteger();
        AtomicInteger conflictCount = new AtomicInteger();
        AtomicInteger updateAttempts = new AtomicInteger();

        ExecutorService pool = Executors.newFixedThreadPool(workers);
        try {
            Runnable edit = () -> {
                try (Connection c = connect()) {
                    c.setAutoCommit(true); // each conditional UPDATE is its own transaction
                    long readVersion;
                    try (PreparedStatement read = c.prepareStatement(
                            "SELECT row_version FROM identity_account WHERE id = ?")) {
                        read.setObject(1, id);
                        try (ResultSet rs = read.executeQuery()) {
                            rs.next();
                            readVersion = rs.getLong(1);
                        }
                    }

                    bothRead.countDown();
                    bothRead.await();      // ensure both read the same version
                    startUpdate.await();   // release both at once

                    updateAttempts.incrementAndGet();
                    int updated;
                    try (PreparedStatement ps = c.prepareStatement(CONDITIONAL_UPDATE)) {
                        // simultaneous editors target DIFFERENT end states; no blind retry
                        ps.setString(1, Thread.currentThread().getName().endsWith("1") ? "ACTIVE" : "SUSPENDED");
                        ps.setObject(2, id);
                        ps.setLong(3, readVersion); // both use the version they read
                        updated = ps.executeUpdate();
                    }

                    if (updated == 1) {
                        successCount.incrementAndGet();
                    } else {
                        conflictCount.incrementAndGet(); // 0 rows -> stale -> conflict
                    }
                } catch (Exception e) {
                    throw new RuntimeException(e);
                }
            };

            // name threads so the two editors choose different targets deterministically
            Future<?> f1 = pool.submit(() -> {
                Thread.currentThread().setName("editor-1");
                edit.run();
            });
            Future<?> f2 = pool.submit(() -> {
                Thread.currentThread().setName("editor-2");
                edit.run();
            });

            // wait until both have read, then release both updates simultaneously
            assertThat(bothRead.await(30, TimeUnit.SECONDS)).isTrue();
            startUpdate.countDown();

            f1.get(30, TimeUnit.SECONDS);
            f2.get(30, TimeUnit.SECONDS);
        } finally {
            pool.shutdownNow();
        }

        // exactly one success / one conflict
        assertThat(successCount.get()).isEqualTo(1);
        assertThat(conflictCount.get()).isEqualTo(1);
        // no blind retry: each worker attempted its update exactly once
        assertThat(updateAttempts.get()).isEqualTo(workers);
        // no lost update: exactly one applied edit; row_version advanced by exactly one
        assertThat(readRowVersion(id)).isEqualTo(1L);
    }

    // ---- helpers ----

    private UUID insertAccount(long rowVersion, String status) throws SQLException {
        UUID id = UUID.randomUUID();
        try (Connection c = connect(); PreparedStatement ps = c.prepareStatement(
                "INSERT INTO identity_account (id, issuer, subject, channel, status, row_version) "
                        + "VALUES (?, ?, ?, 'STAFF', ?, ?)")) {
            ps.setObject(1, id);
            ps.setString(2, "issuer-" + id);
            ps.setString(3, "subject-" + id);
            ps.setString(4, status);
            ps.setLong(5, rowVersion);
            ps.executeUpdate();
        }
        return id;
    }

    private long readRowVersion(UUID id) throws SQLException {
        try (Connection c = connect(); PreparedStatement ps = c.prepareStatement(
                "SELECT row_version FROM identity_account WHERE id = ?")) {
            ps.setObject(1, id);
            try (ResultSet rs = ps.executeQuery()) {
                rs.next();
                return rs.getLong(1);
            }
        }
    }

    private String readStatus(UUID id) throws SQLException {
        try (Connection c = connect(); PreparedStatement ps = c.prepareStatement(
                "SELECT status FROM identity_account WHERE id = ?")) {
            ps.setObject(1, id);
            try (ResultSet rs = ps.executeQuery()) {
                rs.next();
                return rs.getString(1);
            }
        }
    }

    private static Connection connect() throws SQLException {
        return DriverManager.getConnection(jdbcUrl, username, password);
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
