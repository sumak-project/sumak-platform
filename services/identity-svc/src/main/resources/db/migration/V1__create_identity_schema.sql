CREATE TABLE identity_account (
    id UUID PRIMARY KEY,
    issuer TEXT NOT NULL,
    subject TEXT NOT NULL,
    channel TEXT NOT NULL CHECK (channel IN ('CITIZEN', 'STAFF')),
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'ACTIVE', 'SUSPENDED')),
    last_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    row_version BIGINT NOT NULL DEFAULT 0 CHECK (row_version >= 0),
    CONSTRAINT uq_identity_account_issuer_subject UNIQUE (issuer, subject)
);

CREATE TABLE identity_person_link (
    account_id UUID PRIMARY KEY REFERENCES identity_account(id),
    registry_ref UUID,
    staff_directory_ref TEXT,
    proof_ref TEXT NOT NULL,
    verified_at TIMESTAMPTZ NOT NULL,
    method TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    row_version BIGINT NOT NULL DEFAULT 0 CHECK (row_version >= 0),
    CONSTRAINT ck_identity_person_link_owner CHECK (
        (registry_ref IS NOT NULL AND staff_directory_ref IS NULL)
        OR (registry_ref IS NULL AND staff_directory_ref IS NOT NULL)
    ),
    CONSTRAINT uq_identity_person_link_registry UNIQUE (registry_ref),
    CONSTRAINT uq_identity_person_link_staff UNIQUE (staff_directory_ref)
);

CREATE TABLE institutional_role (
    code TEXT PRIMARY KEY CHECK (code IN (
        'CITIZEN',
        'SUPER_ADMINISTRATOR',
        'WORKS_AND_FINANCE_ADMINISTRATOR',
        'INCIDENTS_AND_COMPLAINTS_OPERATOR',
        'SOCIAL_COMMUNICATION_AND_CITIZEN_PARTICIPATION'
    )),
    display_name TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    row_version BIGINT NOT NULL DEFAULT 0 CHECK (row_version >= 0)
);

INSERT INTO institutional_role (code, display_name) VALUES
    ('CITIZEN', 'Citizen'),
    ('SUPER_ADMINISTRATOR', 'Super Administrator'),
    ('WORKS_AND_FINANCE_ADMINISTRATOR', 'Works and Finance Administrator'),
    ('INCIDENTS_AND_COMPLAINTS_OPERATOR', 'Incidents and Complaints Operator'),
    ('SOCIAL_COMMUNICATION_AND_CITIZEN_PARTICIPATION', 'Social Communication and Citizen Participation');

CREATE TABLE role_assignment (
    id UUID PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES identity_account(id),
    role_code TEXT NOT NULL REFERENCES institutional_role(code),
    scope_type TEXT NOT NULL,
    scope_ref TEXT NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL,
    valid_until TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    granted_by_ref TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    row_version BIGINT NOT NULL DEFAULT 0 CHECK (row_version >= 0),
    CONSTRAINT ck_role_assignment_period CHECK (valid_until IS NULL OR valid_until > valid_from)
);

CREATE UNIQUE INDEX uq_role_assignment_active
    ON role_assignment (account_id, role_code, scope_type, scope_ref)
    WHERE revoked_at IS NULL;

CREATE TABLE identity_security_event (
    id UUID PRIMARY KEY,
    account_id UUID REFERENCES identity_account(id),
    kind TEXT NOT NULL,
    outcome TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    reason_code TEXT
);

CREATE TABLE outbox_event (
    id UUID PRIMARY KEY,
    event_type TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version > 0),
    aggregate_ref UUID NOT NULL,
    aggregate_version BIGINT NOT NULL CHECK (aggregate_version >= 0),
    occurred_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL,
    published_at TIMESTAMPTZ
);

CREATE TABLE inbox_event (
    event_id UUID PRIMARY KEY,
    event_type TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK (schema_version > 0),
    received_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMPTZ
);

CREATE TABLE idempotency_record (
    command_id UUID PRIMARY KEY,
    account_id UUID NOT NULL,
    result JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ
);
