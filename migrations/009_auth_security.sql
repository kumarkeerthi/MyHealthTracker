ALTER TABLE users
    ADD COLUMN IF NOT EXISTS email VARCHAR(255),
    ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255),
    ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user' NOT NULL,
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
    ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP NULL;

UPDATE users
SET email = CONCAT('legacy-user-', id, '@myhealthtracker.local')
WHERE email IS NULL;

UPDATE users
SET hashed_password = '$2b$12$9vrnljy35QRA0rA4mHztJ.gS4lnfWKdA1z2x.8NfVxKTwvf6dr0I6'
WHERE hashed_password IS NULL;

ALTER TABLE users
    ALTER COLUMN email SET NOT NULL,
    ALTER COLUMN hashed_password SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users(email);

CREATE TABLE IF NOT EXISTS auth_refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    issued_at TIMESTAMP NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMP NULL,
    replaced_by_token_hash VARCHAR(255) NULL,
    ip_address VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_login_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NULL REFERENCES users(id),
    email VARCHAR(255) NOT NULL,
    ip_address VARCHAR(64) NOT NULL,
    success BOOLEAN NOT NULL,
    attempted_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_auth_login_attempts_email ON auth_login_attempts(email);
CREATE INDEX IF NOT EXISTS idx_auth_login_attempts_user_id ON auth_login_attempts(user_id);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
