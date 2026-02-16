CREATE TABLE IF NOT EXISTS security_audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NULL REFERENCES users(id),
    event_type VARCHAR(80) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'info',
    ip_address VARCHAR(64) NULL,
    route VARCHAR(255) NULL,
    details TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_security_audit_logs_event_type ON security_audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_security_audit_logs_user_id ON security_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_security_audit_logs_created_at ON security_audit_logs(created_at);

CREATE TABLE IF NOT EXISTS llm_usage_daily (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    usage_date DATE NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_llm_usage_daily_user_date UNIQUE(user_id, usage_date)
);

CREATE INDEX IF NOT EXISTS idx_llm_usage_daily_usage_date ON llm_usage_daily(usage_date);
