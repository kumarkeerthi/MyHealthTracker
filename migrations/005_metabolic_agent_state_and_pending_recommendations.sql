CREATE TABLE IF NOT EXISTS metabolic_agent_state (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    last_daily_scan TIMESTAMP NULL,
    last_weekly_scan TIMESTAMP NULL,
    last_monthly_review TIMESTAMP NULL,
    last_carb_adjustment TIMESTAMP NULL,
    last_protein_adjustment TIMESTAMP NULL,
    last_strength_adjustment TIMESTAMP NULL,
    carb_ceiling_current INTEGER NOT NULL DEFAULT 90,
    protein_target_current INTEGER NOT NULL DEFAULT 90,
    fruit_allowance_current INTEGER NOT NULL DEFAULT 1,
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pending_recommendations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cadence VARCHAR(20) NOT NULL,
    recommendation_type VARCHAR(80) NOT NULL,
    title VARCHAR(180) NOT NULL,
    summary VARCHAR(500) NOT NULL,
    confidence_level FLOAT NOT NULL DEFAULT 0.7,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    data_used TEXT NOT NULL,
    threshold_triggered VARCHAR(220) NOT NULL,
    historical_comparison TEXT NOT NULL,
    llm_summary TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS idx_pending_recommendations_user_id ON pending_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_pending_recommendations_status ON pending_recommendations(status);
