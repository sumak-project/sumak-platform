package ec.gob.sumak.identity.application.port;

import java.util.function.Supplier;

public interface IdentityTransaction {
    <T> T required(Supplier<T> work);
}
