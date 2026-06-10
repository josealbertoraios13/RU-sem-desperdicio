-- PostgreSQL schema for SmartRU
-- Note: PostgreSQL enables foreign keys by default

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    role TEXT NOT NULL, -- 'estudante', 'funcionario', 'convidado'
    name TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL, 
    enrollment TEXT UNIQUE, -- Só para estudante/funcionários
    register_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

DO $$
BEGIN
    CREATE TYPE schedule_status AS ENUM ('AGENDADO', 'CONFIRMADO', 'CANCELADO');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS schedules (
    id BIGSERIAL PRIMARY KEY,
    user_cpf TEXT NOT NULL,
    schedule_type TEXT NOT NULL,
    meal_type TEXT NOT NULL DEFAULT 'essencial',
    schedule_date DATE NOT NULL,
    estimated_time TIME,
    reminder_sent BOOLEAN DEFAULT FALSE,
    status schedule_status DEFAULT 'AGENDADO',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    consumed_at TIMESTAMP WITH TIME ZONE,
    confirmed_by BIGINT,
    FOREIGN KEY (user_cpf) REFERENCES users(cpf) ON DELETE CASCADE,
    CHECK (meal_type IN ('select', 'leve_sabor', 'essencial')),
    UNIQUE(user_cpf, schedule_type, schedule_date)
);

CREATE TABLE IF NOT EXISTS consumptions (
    id BIGSERIAL PRIMARY KEY,
    schedule_id BIGINT NOT NULL,
    confirmed_by BIGINT NOT NULL,
    confirmed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE,
    FOREIGN KEY (confirmed_by) REFERENCES users(id) ON DELETE CASCADE
);

-- Table for password reset tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
  id BIGSERIAL PRIMARY KEY,
  user_cpf TEXT NOT NULL,
  token_hash TEXT NOT NULL UNIQUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
  used BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (user_cpf) REFERENCES users(cpf) ON DELETE CASCADE
);

-- Index for faster token lookups
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user_cpf ON password_reset_tokens(user_cpf);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_token_hash ON password_reset_tokens(token_hash);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_cpf ON users(cpf);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_schedules_user_cpf ON schedules(user_cpf);
CREATE INDEX IF NOT EXISTS idx_schedules_date_schedule ON schedules(schedule_date);
CREATE INDEX IF NOT EXISTS idx_schedules_status ON schedules(status);
CREATE INDEX IF NOT EXISTS idx_schedules_date_status ON schedules(schedule_date, status);
CREATE INDEX IF NOT EXISTS idx_schedules_reminder
    ON schedules(schedule_date, estimated_time, reminder_sent)
    WHERE reminder_sent = FALSE;
CREATE INDEX IF NOT EXISTS idx_consumptions_schedule_id ON consumptions(schedule_id);
CREATE INDEX IF NOT EXISTS idx_consumptions_confirmed_by ON consumptions(confirmed_by);

-- Table for weekly menu images (simplified)
CREATE TABLE IF NOT EXISTS menus (
    id BIGSERIAL PRIMARY KEY,
    image_url TEXT NOT NULL,
    filename TEXT NOT NULL,
    lunch_image_url TEXT,
    lunch_filename TEXT,
    dinner_image_url TEXT,
    dinner_filename TEXT,
    uploaded_by BIGINT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_menus_uploaded_at ON menus(uploaded_at DESC);

-- Notification system tables
CREATE TABLE IF NOT EXISTS device_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_cpf TEXT NOT NULL,
    token TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'android',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_cpf) REFERENCES users(cpf) ON DELETE CASCADE,
    UNIQUE(token)
);

CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    user_cpf TEXT NOT NULL,
    channel TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    job_id BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_cpf) REFERENCES users(cpf) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notification_jobs (
    id BIGSERIAL PRIMARY KEY,
    job_type TEXT NOT NULL DEFAULT 'daily_reminder',
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    executed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL DEFAULT 'scheduled',
    total_users INTEGER NOT NULL DEFAULT 0,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notification_templates (
    id BIGSERIAL PRIMARY KEY,
    template_key TEXT NOT NULL UNIQUE,
    title_template TEXT NOT NULL,
    body_template TEXT NOT NULL,
    channel TEXT NOT NULL DEFAULT 'push',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scheduler_locks (
    lock_name TEXT PRIMARY KEY,
    locked_by TEXT NOT NULL,
    locked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_device_tokens_user_cpf ON device_tokens(user_cpf);
CREATE INDEX IF NOT EXISTS idx_device_tokens_active ON device_tokens(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_notifications_user_cpf ON notifications(user_cpf);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_job_id ON notifications(job_id);
CREATE INDEX IF NOT EXISTS idx_notifications_next_retry
    ON notifications(next_retry_at)
    WHERE status = 'failed' AND next_retry_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_notification_jobs_type_status ON notification_jobs(job_type, status);
CREATE INDEX IF NOT EXISTS idx_notification_jobs_scheduled ON notification_jobs(scheduled_at);

INSERT INTO notification_templates (template_key, title_template, body_template, channel)
VALUES (
    'daily_reminder_push',
    'FilaRural - Ola, {nome}!',
    'Ja estas indo para o RU? Consulta a fila no FilaRural e ajuda outros estudantes colaborando em tempo real.',
    'push'
) ON CONFLICT (template_key) DO NOTHING;

INSERT INTO notification_templates (template_key, title_template, body_template, channel)
VALUES (
    'daily_reminder_email',
    'FilaRural - Hora do RU!',
    'Ola, {nome}!<br><br>Ja estas indo para o Restaurante Universitario?<br><br>Consulta a fila no FilaRural e ajuda outros estudantes colaborando em tempo real.<br><br>Acesse: <a href="{app_url}">{app_url}</a>',
    'email'
) ON CONFLICT (template_key) DO NOTHING;

-- Legacy table for weekly menu images (kept for backward compatibility)
CREATE TABLE IF NOT EXISTS menu_images (
    id BIGSERIAL PRIMARY KEY,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    week_reference TEXT NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    uploaded_by BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Only one active menu at a time (enforced at DB level)
CREATE UNIQUE INDEX IF NOT EXISTS idx_menu_images_unique_active
    ON menu_images(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_menu_images_is_active ON menu_images(is_active);
CREATE INDEX IF NOT EXISTS idx_menu_images_week ON menu_images(week_reference);
