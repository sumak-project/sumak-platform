package ec.gob.sumak.identity.domain;

import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

public final class IdentityAccount {
    private final UUID id;
    private final OidcIdentity oidcIdentity;
    private final IdentityChannel channel;
    private final List<RoleAssignment> assignments;
    private AccountStatus status;
    private long version;

    private IdentityAccount(
            UUID id,
            OidcIdentity oidcIdentity,
            IdentityChannel channel,
            AccountStatus status,
            long version,
            List<RoleAssignment> assignments) {
        this.id = Objects.requireNonNull(id, "id");
        this.oidcIdentity = Objects.requireNonNull(oidcIdentity, "oidcIdentity");
        this.channel = Objects.requireNonNull(channel, "channel");
        this.status = Objects.requireNonNull(status, "status");
        if (version < 0) {
            throw new IllegalArgumentException("version must not be negative");
        }
        this.version = version;
        this.assignments = new ArrayList<>(Objects.requireNonNull(assignments, "assignments"));
    }

    public static IdentityAccount linkInstitutional(UUID id, OidcIdentity identity) {
        return new IdentityAccount(id, identity, IdentityChannel.STAFF, AccountStatus.PENDING, 0, List.of());
    }

    public static IdentityAccount restore(
            UUID id,
            OidcIdentity identity,
            IdentityChannel channel,
            AccountStatus status,
            long version,
            List<RoleAssignment> assignments) {
        return new IdentityAccount(id, identity, channel, status, version, assignments);
    }

    public void activate() {
        ensureNotSuspended();
        status = AccountStatus.ACTIVE;
        version++;
    }

    public void suspend() {
        status = AccountStatus.SUSPENDED;
        version++;
    }

    public void assign(RoleAssignment assignment, Instant now) {
        Objects.requireNonNull(assignment, "assignment");
        Objects.requireNonNull(now, "now");
        ensureActive();
        boolean duplicate = assignments.stream()
                .filter(existing -> existing.isActiveAt(now))
                .anyMatch(existing -> existing.role() == assignment.role()
                        && existing.scopeType().equals(assignment.scopeType())
                        && existing.scopeRef().equals(assignment.scopeRef()));
        if (duplicate) {
            throw new IllegalStateException("an active assignment already exists for role and scope");
        }
        assignments.add(assignment);
        version++;
    }

    public boolean isAuthorized(InstitutionalRole role, String scopeType, String scopeRef, Instant now) {
        if (status != AccountStatus.ACTIVE) {
            return false;
        }
        return assignments.stream().anyMatch(assignment ->
                assignment.role() == role
                        && assignment.scopeType().equals(scopeType)
                        && assignment.scopeRef().equals(scopeRef)
                        && assignment.isActiveAt(now));
    }

    private void ensureActive() {
        if (status != AccountStatus.ACTIVE) {
            throw new IllegalStateException("account must be active");
        }
    }

    private void ensureNotSuspended() {
        if (status == AccountStatus.SUSPENDED) {
            throw new IllegalStateException("a suspended account cannot be activated without review");
        }
    }

    public UUID id() {
        return id;
    }

    public OidcIdentity oidcIdentity() {
        return oidcIdentity;
    }

    public IdentityChannel channel() {
        return channel;
    }

    public AccountStatus status() {
        return status;
    }

    public long version() {
        return version;
    }

    public List<RoleAssignment> assignments() {
        return Collections.unmodifiableList(assignments);
    }
}
