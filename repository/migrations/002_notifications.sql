-- =============================================================
-- Migration 002: Smart Notification System
-- Applied to: Existing databases (schema.sql already has these
--             for new installations)
-- =============================================================

-- 1. DEVICE PUSH TOKENS
CREATE TABLE IF NOT EXISTS device_tokens (
    id              BIGSERIAL PRIMARY KEY,
    user_cpf        TEXT NOT NULL,
    token           TEXT NOT NULL,
    platform        TEXT NOT NULL DEFAULT 'android',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_cpf) REFERENCES users(cpf) ON DELETE CASCADE,
    UNIQUE(token)
);

-- 2. NOTIFICATION LOG
CREATE TABLE IF NOT EXISTS notifications (
    id              BIGSERIAL PRIMARY KEY,
    user_cpf        TEXT NOT NULL,
    channel         TEXT NOT NULL,
    title           TEXT NOT NULL,
    message         TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    sent_at         TIMESTAMP WITH TIME ZONE,
    error_message   TEXT,
    retry_count     INTEGER NOT NULL DEFAULT 0,
    max_retries     INTEGER NOT NULL DEFAULT 3,
    next_retry_at   TIMESTAMP WITH TIME ZONE,
    job_id          BIGINT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_cpf) REFERENCES users(cpf) ON DELETE CASCADE
);

-- 3. NOTIFICATION JOBS
CREATE TABLE IF NOT EXISTS notification_jobs (
    id              BIGSERIAL PRIMARY KEY,
    job_type        TEXT NOT NULL DEFAULT 'daily_reminder',
    scheduled_at    TIMESTAMP WITH TIME ZONE NOT NULL,
    executed_at     TIMESTAMP WITH TIME ZONE,
    completed_at    TIMESTAMP WITH TIME ZONE,
    status          TEXT NOT NULL DEFAULT 'scheduled',
    total_users     INTEGER NOT NULL DEFAULT 0,
    success_count   INTEGER NOT NULL DEFAULT 0,
    failure_count   INTEGER NOT NULL DEFAULT 0,
    error_message   TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. NOTIFICATION TEMPLATES
CREATE TABLE IF NOT EXISTS notification_templates (
    id              BIGSERIAL PRIMARY KEY,
    template_key    TEXT NOT NULL UNIQUE,
    title_template  TEXT NOT NULL,
    body_template   TEXT NOT NULL,
    channel         TEXT NOT NULL DEFAULT 'push',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. SCHEDULER LOCKS
CREATE TABLE IF NOT EXISTS scheduler_locks (
    lock_name       TEXT PRIMARY KEY,
    locked_by       TEXT NOT NULL,
    locked_at       TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at      TIMESTAMP WITH TIME ZONE NOT NULL
);

-- =============================================================
-- INDEXES
-- =============================================================
CREATE INDEX IF NOT EXISTS idx_device_tokens_user_cpf ON device_tokens(user_cpf);
CREATE INDEX IF NOT EXISTS idx_device_tokens_active ON device_tokens(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_notifications_user_cpf ON notifications(user_cpf);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_job_id ON notifications(job_id);
CREATE INDEX IF NOT EXISTS idx_notifications_next_retry ON notifications(next_retry_at) WHERE status = 'failed' AND next_retry_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_notification_jobs_type_status ON notification_jobs(job_type, status);
CREATE INDEX IF NOT EXISTS idx_notification_jobs_scheduled ON notification_jobs(scheduled_at);

-- =============================================================
-- DEFAULT TEMPLATES
-- =============================================================
INSERT INTO notification_templates (template_key, title_template, body_template, channel)
VALUES (
    'daily_reminder_push',
    'FilaRural - Olá, {nome}! 🍽️',
    'Já estás indo para o RU? Consulta a fila no FilaRural e ajuda outros estudantes colaborando em tempo real.',
    'push'
) ON CONFLICT (template_key) DO NOTHING;

INSERT INTO notification_templates (template_key, title_template, body_template, channel)
VALUES (
    'daily_reminder_email',
    'FilaRural - Hora do RU! 🍽️',
    'Olá, {nome}!<br><br>Já estás indo para o Restaurante Universitário?<br><br>Consulta a fila no FilaRural e ajuda outros estudantes colaborando em tempo real.<br><br>Acesse: <a href="{app_url}">{app_url}</a>',
    'email'
) ON CONFLICT (template_key) DO NOTHING;
