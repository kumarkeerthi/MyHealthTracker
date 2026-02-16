CREATE TABLE IF NOT EXISTS metabolic_recommendation_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    waist_not_dropping BOOLEAN DEFAULT FALSE,
    strength_increasing BOOLEAN DEFAULT FALSE,
    carb_ceiling_before INTEGER NOT NULL,
    carb_ceiling_after INTEGER NOT NULL,
    protein_target_min_before INTEGER NOT NULL,
    protein_target_min_after INTEGER NOT NULL,
    recommend_strength_volume_increase BOOLEAN DEFAULT FALSE,
    allow_refeed_meal BOOLEAN DEFAULT FALSE,
    recommendations TEXT NOT NULL,
    advisor_report TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_metabolic_recommendation_logs_user_created
    ON metabolic_recommendation_logs (user_id, created_at DESC);
