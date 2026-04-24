-- PostgreSQL schema for SmartRU
-- Note: PostgreSQL enables foreign keys by default

CREATE TABLE IF NOT EXISTS usuarios (
    id BIGSERIAL PRIMARY KEY,
    tipo_usuario TEXT NOT NULL, -- 'aluno', 'funcionario', 'convidado'
    nome_completo TEXT NOT NULL,
    cpf TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL, -- String de 6 números (hashed)
    matricula TEXT UNIQUE, -- Só para alunos
    codigo_funcionario TEXT UNIQUE, -- Só para funcionários
    data_cadastro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agendamentos (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT NOT NULL,
    tipo_refeicao TEXT NOT NULL, -- 'almoco' ou 'jantar'
    data_refeicao DATE NOT NULL,
    horario_estimado TIME,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE(usuario_id, tipo_refeicao, data_refeicao) -- Impede agendamento duplo
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_usuarios_cpf ON usuarios(cpf);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_agendamentos_usuario_id ON agendamentos(usuario_id);
CREATE INDEX IF NOT EXISTS idx_agendamentos_data_refeicao ON agendamentos(data_refeicao);