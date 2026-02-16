CREATE TABLE IF NOT EXISTS recipes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(160) NOT NULL UNIQUE,
    ingredients VARCHAR(800) NOT NULL,
    protein DOUBLE PRECISION NOT NULL,
    carbs DOUBLE PRECISION NOT NULL,
    fats DOUBLE PRECISION NOT NULL,
    cooking_time_minutes INTEGER NOT NULL,
    oil_usage_tsp DOUBLE PRECISION NOT NULL,
    insulin_score_impact DOUBLE PRECISION NOT NULL,
    external_link_primary VARCHAR(300),
    external_link_secondary VARCHAR(300)
);
