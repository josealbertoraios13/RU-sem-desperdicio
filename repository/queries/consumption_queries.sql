-- ============================================================
-- MODELAGEM DE DADOS - CONTROLE DE CONSUMO SMARTRU
-- ============================================================

-- 1. CRIAÇÃO DO TIPO ENUM PARA STATUS
CREATE TYPE schedule_status AS ENUM ('AGENDADO', 'CONFIRMADO', 'CANCELADO');

-- 2. TABELA DE AGENDAMENTOS (ATUALIZADA)
CREATE TABLE IF NOT EXISTS schedules (
    id BIGSERIAL PRIMARY KEY,
    user_cpf TEXT NOT NULL,
    schedule_type TEXT NOT NULL,
    schedule_date DATE NOT NULL,
    estimated_time TIME,
    status schedule_status DEFAULT 'AGENDADO',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    consumed_at TIMESTAMP WITH TIME ZONE,
    confirmed_by BIGINT,
    FOREIGN KEY (user_cpf) REFERENCES users(cpf) ON DELETE CASCADE,
    UNIQUE(user_cpf, schedule_type, schedule_date)
);

-- 3. TABELA DE CONSUMOS (HISTÓRICO)
CREATE TABLE IF NOT EXISTS consumptions (
    id BIGSERIAL PRIMARY KEY,
    schedule_id BIGINT NOT NULL,
    confirmed_by BIGINT NOT NULL,
    confirmed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE,
    FOREIGN KEY (confirmed_by) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. ÍNDICES PARA PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_schedules_status ON schedules(status);
CREATE INDEX IF NOT EXISTS idx_schedules_date_status ON schedules(schedule_date, status);
CREATE INDEX IF NOT EXISTS idx_consumptions_schedule_id ON consumptions(schedule_id);
CREATE INDEX IF NOT EXISTS idx_consumptions_confirmed_by ON consumptions(confirmed_by);

-- ============================================================
-- QUERIES DE RELATÓRIO
-- ============================================================

-- RELATÓRIO 1: RESUMO DO DIA (AGENDADOS, CONSUMIDOS, NO-SHOWS)
SELECT
    schedule_date,
    COUNT(*) AS total_agendados,
    COUNT(*) FILTER (WHERE status = 'CONFIRMADO') AS consumidos,
    COUNT(*) - COUNT(*) FILTER (WHERE status = 'CONFIRMADO') AS no_shows
FROM schedules
WHERE schedule_date = CURRENT_DATE
GROUP BY schedule_date;

-- RELATÓRIO 2: DETALHAMENTO COM DADOS DO ALUNO
SELECT 
    s.id,
    u.name AS nome_aluno,
    u.cpf,
    s.schedule_type,
    s.schedule_date,
    s.status,
    s.estimated_time,
    s.created_at,
    s.consumed_at,
    conf.name AS confirmado_por
FROM schedules s
JOIN users u ON u.cpf = s.user_cpf
LEFT JOIN users conf ON s.confirmed_by = conf.id
WHERE s.schedule_date = CURRENT_DATE
ORDER BY s.schedule_type, s.estimated_time;

-- RELATÓRIO 3: HISTÓRICO POR PERÍODO
SELECT
    schedule_date,
    schedule_type,
    COUNT(*) AS total_agendados,
    COUNT(*) FILTER (WHERE status = 'CONFIRMADO') AS consumidos,
    COUNT(*) - COUNT(*) FILTER (WHERE status = 'CONFIRMADO') AS no_shows
FROM schedules
WHERE schedule_date BETWEEN '2026-05-01' AND '2026-05-31'
GROUP BY schedule_date, schedule_type
ORDER BY schedule_date, schedule_type;

-- RELATÓRIO 4: TAXA DE COMPARECIMENTO
SELECT 
    schedule_date,
    ROUND(
        COUNT(*) FILTER (WHERE status = 'CONFIRMADO')::NUMERIC / 
        NULLIF(COUNT(*), 0) * 100, 
        2
    ) AS taxa_comparecimento_pct
FROM schedules
WHERE schedule_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY schedule_date
ORDER BY schedule_date DESC;
