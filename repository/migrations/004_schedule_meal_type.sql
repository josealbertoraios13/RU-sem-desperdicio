-- Adds the required meal type chosen during schedule creation.

ALTER TABLE schedules
ADD COLUMN IF NOT EXISTS meal_type TEXT NOT NULL DEFAULT 'essencial';

UPDATE schedules
SET meal_type = 'essencial'
WHERE meal_type IS NULL;

DO $$
BEGIN
    ALTER TABLE schedules
    ADD CONSTRAINT schedules_meal_type_check
    CHECK (meal_type IN ('select', 'leve_sabor', 'essencial'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;
