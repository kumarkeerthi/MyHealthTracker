CREATE TABLE IF NOT EXISTS metabolic_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    protein_target_min INTEGER DEFAULT 90,
    protein_target_max INTEGER DEFAULT 110,
    carb_ceiling INTEGER DEFAULT 90,
    oil_limit_tsp FLOAT DEFAULT 3,
    fasting_start_time VARCHAR(5) DEFAULT '14:00',
    fasting_end_time VARCHAR(5) DEFAULT '08:00',
    max_chapati_per_day INTEGER DEFAULT 2,
    allow_rice BOOLEAN DEFAULT FALSE,
    chocolate_limit_per_day INTEGER DEFAULT 2,
    insulin_score_green_threshold FLOAT DEFAULT 40,
    insulin_score_yellow_threshold FLOAT DEFAULT 70,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'exercise_category_enum') THEN
        CREATE TYPE exercise_category_enum AS ENUM ('WALK', 'BODYWEIGHT', 'MONKEY_BAR', 'STRENGTH');
    END IF;
END$$;

ALTER TABLE exercise_entries
    ADD COLUMN IF NOT EXISTS exercise_category exercise_category_enum DEFAULT 'STRENGTH',
    ADD COLUMN IF NOT EXISTS movement_type VARCHAR(120) DEFAULT 'general',
    ADD COLUMN IF NOT EXISTS reps INTEGER,
    ADD COLUMN IF NOT EXISTS sets INTEGER,
    ADD COLUMN IF NOT EXISTS perceived_intensity INTEGER DEFAULT 5,
    ADD COLUMN IF NOT EXISTS step_count INTEGER,
    ADD COLUMN IF NOT EXISTS calories_estimate FLOAT;

ALTER TABLE vitals_entries
    ADD COLUMN IF NOT EXISTS resting_hr FLOAT,
    ADD COLUMN IF NOT EXISTS sleep_hours FLOAT,
    ADD COLUMN IF NOT EXISTS waist_cm FLOAT,
    ADD COLUMN IF NOT EXISTS hrv FLOAT,
    ADD COLUMN IF NOT EXISTS steps_total INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS body_fat_percentage FLOAT;

INSERT INTO metabolic_profiles (
    user_id,
    protein_target_min,
    protein_target_max,
    carb_ceiling,
    oil_limit_tsp,
    fasting_start_time,
    fasting_end_time,
    max_chapati_per_day,
    allow_rice,
    chocolate_limit_per_day,
    insulin_score_green_threshold,
    insulin_score_yellow_threshold
)
SELECT
    u.id,
    90,
    110,
    90,
    3,
    '14:00',
    '08:00',
    2,
    FALSE,
    2,
    40,
    70
FROM users u
LEFT JOIN metabolic_profiles mp ON mp.user_id = u.id
WHERE mp.id IS NULL;
