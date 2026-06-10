-- ATENÇÃO: executar esta migration antes de subir para produção.
-- Adiciona controle de lembrete de agendamento na tabela schedules.
--
-- Efeitos:
--   1. Nova coluna reminder_sent (default FALSE) — impede lembretes duplicados
--   2. Índice parcial em (schedule_date, estimated_time) filtrando
--      apenas reminder_sent = FALSE — queries do job ficam rápidas
--      e o índice encolhe automaticamente conforme os lembretes são enviados

ALTER TABLE schedules
    ADD COLUMN IF NOT EXISTS reminder_sent BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_schedules_reminder
    ON schedules(schedule_date, estimated_time, reminder_sent)
    WHERE reminder_sent = FALSE;