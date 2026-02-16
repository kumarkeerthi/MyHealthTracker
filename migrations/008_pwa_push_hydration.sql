ALTER TABLE daily_logs
    ADD COLUMN IF NOT EXISTS water_ml INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS hydration_score FLOAT DEFAULT 0.0;

ALTER TABLE notification_settings
    ADD COLUMN IF NOT EXISTS protein_reminders_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS fasting_alerts_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS hydration_alerts_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS insulin_alerts_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS strength_reminders_enabled BOOLEAN DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS quiet_hours_start VARCHAR(5),
    ADD COLUMN IF NOT EXISTS quiet_hours_end VARCHAR(5);

CREATE TABLE IF NOT EXISTS push_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    endpoint VARCHAR(600) NOT NULL UNIQUE,
    p256dh VARCHAR(255) NOT NULL,
    auth VARCHAR(255) NOT NULL,
    expiration_time TIMESTAMP NULL,
    user_agent VARCHAR(255) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
