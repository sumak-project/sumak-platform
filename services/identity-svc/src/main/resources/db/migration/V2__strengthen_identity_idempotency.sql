ALTER TABLE idempotency_record
    ADD COLUMN scope_key VARCHAR(160),
    ADD COLUMN operation VARCHAR(80),
    ADD COLUMN request_digest CHAR(64),
    ADD COLUMN resource_ref UUID,
    ADD COLUMN status VARCHAR(16);

UPDATE idempotency_record
SET scope_key = 'legacy',
    operation = 'legacy',
    request_digest = repeat('0', 64),
    resource_ref = account_id,
    status = 'COMPLETED';

ALTER TABLE idempotency_record
    ALTER COLUMN scope_key SET NOT NULL,
    ALTER COLUMN operation SET NOT NULL,
    ALTER COLUMN request_digest SET NOT NULL,
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN status SET DEFAULT 'PENDING',
    ALTER COLUMN account_id DROP NOT NULL,
    ALTER COLUMN result DROP NOT NULL,
    DROP CONSTRAINT idempotency_record_pkey,
    ADD CONSTRAINT idempotency_record_pkey PRIMARY KEY (scope_key, operation, command_id),
    ADD CONSTRAINT ck_idempotency_record_digest CHECK (request_digest ~ '^[0-9a-f]{64}$'),
    ADD CONSTRAINT ck_idempotency_record_status CHECK (status IN ('PENDING', 'COMPLETED'));

CREATE INDEX ix_idempotency_record_expires_at
    ON idempotency_record (expires_at);

CREATE INDEX ix_idempotency_record_status_created_at
    ON idempotency_record (status, created_at);
