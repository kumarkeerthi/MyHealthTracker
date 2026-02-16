ALTER TABLE meal_entries
    ADD COLUMN IF NOT EXISTS image_url VARCHAR(500),
    ADD COLUMN IF NOT EXISTS vision_confidence FLOAT,
    ADD COLUMN IF NOT EXISTS manual_adjustment_flag BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS portion_scale_factor FLOAT;
