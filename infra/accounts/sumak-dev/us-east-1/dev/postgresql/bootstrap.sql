\set ON_ERROR_STOP on

CREATE ROLE identity_owner NOLOGIN;
CREATE ROLE identity_migration LOGIN PASSWORD :'identity_migration_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
CREATE ROLE identity_runtime LOGIN PASSWORD :'identity_runtime_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
CREATE DATABASE sumak_identity OWNER identity_owner;
\connect sumak_identity
REVOKE CONNECT, TEMPORARY ON DATABASE sumak_identity FROM PUBLIC;
GRANT CONNECT ON DATABASE sumak_identity TO identity_migration, identity_runtime;
GRANT identity_owner TO identity_migration;
ALTER DEFAULT PRIVILEGES FOR ROLE identity_owner IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO identity_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE identity_owner IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO identity_runtime;

\connect postgres
CREATE ROLE config_owner NOLOGIN;
CREATE ROLE config_migration LOGIN PASSWORD :'config_migration_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
CREATE ROLE config_runtime LOGIN PASSWORD :'config_runtime_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
CREATE DATABASE sumak_config OWNER config_owner;
\connect sumak_config
REVOKE CONNECT, TEMPORARY ON DATABASE sumak_config FROM PUBLIC;
GRANT CONNECT ON DATABASE sumak_config TO config_migration, config_runtime;
GRANT config_owner TO config_migration;
ALTER DEFAULT PRIVILEGES FOR ROLE config_owner IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO config_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE config_owner IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO config_runtime;
