DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type
        WHERE typname = 'metabolic_phase_enum'
    ) THEN
        CREATE TYPE metabolic_phase_enum AS ENUM (
            'RESET',
            'STABILIZATION',
            'RECOMPOSITION',
            'PERFORMANCE',
            'MAINTENANCE'
        );
    END IF;
END $$;

ALTER TABLE metabolic_agent_state
    ADD COLUMN IF NOT EXISTS metabolic_phase metabolic_phase_enum NOT NULL DEFAULT 'RESET';

ALTER TABLE metabolic_agent_state
    ADD COLUMN IF NOT EXISTS metabolic_identity VARCHAR(40) NOT NULL DEFAULT 'Repair Mode';
