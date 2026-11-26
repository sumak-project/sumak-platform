package ec.gob.sumak.identity.application.port;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatIllegalArgumentException;
import static org.assertj.core.api.Assertions.assertThatNullPointerException;

import java.util.UUID;
import org.junit.jupiter.api.Test;

/**
 * SCRUM-60 — Idempotency key contract (unit, no DB, no AWS).
 *
 * <p>Authoritative schema (docs/10_Datos/identity-svc.md, INVENTARIO_TABLAS_SQL_150.csv):
 * {@code idempotency_record(scope_key, operation, command_id, ...)},
 * PK(scope_key, operation, command_id). This record mirrors that key.
 *
 * <p>Acceptance: key is scope + operation + commandId. Two keys are equal only when
 * all three components are equal; changing any one component yields a distinct key,
 * so distinct scopes/operations/commandIds never collide on the same record.
 */
class IdempotencyKeyTest {

    private static final UUID COMMAND_ID = UUID.fromString("11111111-1111-1111-1111-111111111111");

    @Test
    void keyIsScopeKeyOperationAndCommandId() {
        var key = new IdempotencyKey("identity-svc", "LinkInstitutionalUser", COMMAND_ID);

        assertThat(key.scopeKey()).isEqualTo("identity-svc");
        assertThat(key.operation()).isEqualTo("LinkInstitutionalUser");
        assertThat(key.commandId()).isEqualTo(COMMAND_ID);
    }

    @Test
    void equalityRequiresAllThreeComponents() {
        var key = new IdempotencyKey("identity-svc", "LinkInstitutionalUser", COMMAND_ID);

        assertThat(key)
                .isEqualTo(new IdempotencyKey("identity-svc", "LinkInstitutionalUser", COMMAND_ID))
                .hasSameHashCodeAs(new IdempotencyKey("identity-svc", "LinkInstitutionalUser", COMMAND_ID));
    }

    @Test
    void sameCommandIdWithDifferentScopeKeyIsNotEqual() {
        var a = new IdempotencyKey("identity-svc", "LinkInstitutionalUser", COMMAND_ID);
        var b = new IdempotencyKey("other-scope", "LinkInstitutionalUser", COMMAND_ID);

        assertThat(a).isNotEqualTo(b);
        assertThat(a.hashCode()).isNotEqualTo(b.hashCode());
    }

    @Test
    void sameCommandIdWithDifferentOperationIsNotEqual() {
        var a = new IdempotencyKey("identity-svc", "LinkInstitutionalUser", COMMAND_ID);
        var b = new IdempotencyKey("identity-svc", "AssignRole", COMMAND_ID);

        assertThat(a).isNotEqualTo(b);
        assertThat(a.hashCode()).isNotEqualTo(b.hashCode());
    }

    @Test
    void sameScopeKeyAndOperationWithDifferentCommandIdIsNotEqual() {
        var a = new IdempotencyKey("identity-svc", "LinkInstitutionalUser", COMMAND_ID);
        var b = new IdempotencyKey("identity-svc", "LinkInstitutionalUser", UUID.randomUUID());

        assertThat(a).isNotEqualTo(b);
    }

    @Test
    void rejectsNullComponents() {
        assertThatNullPointerException()
                .isThrownBy(() -> new IdempotencyKey(null, "LinkInstitutionalUser", COMMAND_ID));
        assertThatNullPointerException()
                .isThrownBy(() -> new IdempotencyKey("identity-svc", null, COMMAND_ID));
        assertThatNullPointerException()
                .isThrownBy(() -> new IdempotencyKey("identity-svc", "LinkInstitutionalUser", null));
    }

    @Test
    void rejectsBlankScopeKeyAndOperation() {
        assertThatIllegalArgumentException()
                .isThrownBy(() -> new IdempotencyKey(" ", "LinkInstitutionalUser", COMMAND_ID));
        assertThatIllegalArgumentException()
                .isThrownBy(() -> new IdempotencyKey("identity-svc", "", COMMAND_ID));
        assertThatIllegalArgumentException()
                .isThrownBy(() -> new IdempotencyKey("identity-svc", "  ", COMMAND_ID));
    }
}
