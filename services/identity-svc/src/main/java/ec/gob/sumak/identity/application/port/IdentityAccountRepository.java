package ec.gob.sumak.identity.application.port;

import ec.gob.sumak.identity.domain.IdentityAccount;
import ec.gob.sumak.identity.domain.OidcIdentity;
import java.util.Optional;
import java.util.UUID;

public interface IdentityAccountRepository {
    Optional<IdentityAccount> findById(UUID accountId);

    boolean existsByOidcIdentity(OidcIdentity identity);

    void save(IdentityAccount account, long expectedVersion);
}
