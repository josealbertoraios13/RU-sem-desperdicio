-- Consultas de Relatório para Controle de Consumo

-- 1. Total de agendados no dia
SELECT COUNT(*) AS total_agendados
FROM schedules
WHERE schedule_date = CURRENT_DATE;

-- 2. Total de consumidos no dia
SELECT COUNT(*) AS total_consumidos
FROM schedules
WHERE schedule_date = CURRENT_DATE
  AND status = 'CONFIRMADO';

-- 3. Diferença (no-shows)
SELECT
    COUNT(*) AS total_agendados,
    COUNT(*) FILTER (WHERE status = 'CONFIRMADO') AS total_consumidos,
    COUNT(*) - COUNT(*) FILTER (WHERE status = 'CONFIRMADO') AS no_shows
FROM schedules
WHERE schedule_date = CURRENT_DATE;

-- Relatório consolidado por tipo de agendamento e tipo de refeição
SELECT
    schedule_type,
    meal_type,
    COUNT(*) AS total_agendados,
    COUNT(*) FILTER (WHERE status = 'CONFIRMADO') AS consumidos,
    COUNT(*) - COUNT(*) FILTER (WHERE status = 'CONFIRMADO') AS no_shows
FROM schedules
WHERE schedule_date = CURRENT_DATE
GROUP BY schedule_type, meal_type;

-- Histórico de consumo por período
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

-- Detalhamento de todos os agendamentos do dia com status
SELECT 
    s.id,
    u.name AS nome_aluno,
    u.cpf,
    s.schedule_type,
    s.schedule_date,
    s.status,
    s.created_at,
    s.consumed_at,
    conf.name AS confirmado_por
FROM schedules s
JOIN users u ON u.cpf = s.user_cpf
LEFT JOIN users conf ON s.confirmed_by = conf.id
WHERE s.schedule_date = CURRENT_DATE
ORDER BY s.schedule_type, s.estimated_time;

-- Taxa de comparecimento por dia
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
