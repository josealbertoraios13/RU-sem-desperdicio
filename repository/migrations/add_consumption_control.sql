-- Migration script para adicionar controle de consumo
-- Executar em sequência para atualizar banco existente

-- 1. Criar enum de status
DO $$ BEGIN
    CREATE TYPE schedule_status AS ENUM ('AGENDADO', 'CONFIRMADO', 'CANCELADO');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Adicionar colunas de controle na tabela schedules
ALTER TABLE schedules 
ADD COLUMN IF NOT EXISTS status schedule_status DEFAULT 'AGENDADO';

ALTER TABLE schedules 
ADD COLUMN IF NOT EXISTS consumed_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE schedules 
ADD COLUMN IF NOT EXISTS confirmed_by BIGINT;

-- 3. Criar tabela de consumptions (histórico)
CREATE TABLE IF NOT EXISTS consumptions (
    id BIGSERIAL PRIMARY KEY,
    schedule_id BIGINT NOT NULL,
    confirmed_by BIGINT NOT NULL,
    confirmed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE,
    FOREIGN KEY (confirmed_by) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_schedules_status ON schedules(status);
CREATE INDEX IF NOT EXISTS idx_schedules_date_status ON schedules(schedule_date, status);
CREATE INDEX IF NOT EXISTS idx_consumptions_schedule_id ON consumptions(schedule_id);
CREATE INDEX IF NOT EXISTS idx_consumptions_confirmed_by ON consumptions(confirmed_by);

-- 5. Atualizar registros existentes para 'AGENDADO'
UPDATE schedules 
SET status = 'AGENDADO' 
WHERE status IS NULL;
