# Seed System - SmartRU

Sistema de seeding modular, idempotente e seguro para popular ambientes de desenvolvimento, homologação e testes com dados realistas.

## 📋 Visão Geral

O sistema de seeding permite:
- ✅ Popular automaticamente o banco com dados de desenvolvimento
- ✅ Executar seeds de forma idempotente (evita duplicados)
- ✅ Executar seeds completos ou parciais por módulo
- ✅ Logs claros de execução
- ✅ Tratamento de erros robusto
- ✅ Funcionar em ambientes locais e staging

## 🏗️ Arquitetura

```
seeders/
├── __init__.py # exports do pacote
├── base_seeder.py # classe base abstrata
├── user_seeder.py # seed de usuários
├── schedule_seeder.py # seed de schedules
├── seeder_runner.py # orquestrador de seeds
└── README.md # esta documentação
```

### Hierarquia

```
BaseSeeder (abstrato)
├── UserSeeder
└── ScheduleSeeder

SeederRunner (orquestrador)
```

## 🚀 Como Executar

### Via API (Recomendado)

O endpoint requer autenticação via API Key (variável `ADMIN_API_KEY`).

```bash
# Executar todos os seeds
curl -X POST http://localhost:8000/seed/ \
  -H "Authorization: Bearer <ADMIN_API_KEY>"

# Executar seed específico
curl -X POST "http://localhost:8000/seed/?seed_name=user" \
  -H "Authorization: Bearer <ADMIN_API_KEY>"

# Executar múltiplos seeds
curl -X POST "http://localhost:8000/seed/?seeds=user,schedule" \
  -H "Authorization: Bearer <ADMIN_API_KEY>"

# Verificar status
curl http://localhost:8000/seed/status \
  -H "Authorization: Bearer <ADMIN_API_KEY>"
```

### Auto-execução

Os seeds são executados automaticamente 2 segundos após a inicialização da servidor (configurável via variável de ambiente).

## 📊 Seeds Disponíveis

### User Seeder
- **Descrição**: Popula a tabela de usuários
- **Dados**: 30 estudantes + 4 funcionários
- **Idempotência**: Verifica CPF antes de inserir
- **Senha padrão**: `SmartRU2026!`

### Schedule Seeder
- **Descrição**: Cria schedules de exemplo
- **Dados**: Almoço e jantar para próximos dias úteis
- **Idempotência**: Verifica (cpf, tipo, data) antes de inserir
- **Dependência**: Usuários existentes

## 🔧 Configuração

### Variáveis de Ambiente

```bash
# Controla auto-execução na inicialização
RUN_SEED_ON_STARTUP=true # default: true

# Admin API Key para autenticação do endpoint (obrigatório)
ADMIN_API_KEY=change_this_to_a_secure_random_value

# Outros (herdados do .env)
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=smart_ru
```

### Produção vs Desenvolvimento

Em produção, desative a auto-execução:
```bash
RUN_SEED_ON_STARTUP=false
```

## 📝 Adicionando Novos Seeds

1. Crie novo arquivo `seeders/<nome>_seeder.py`
2. Implemente a classe abstrata `BaseSeeder`
3. Registre no `__init__.py`
4. Execute via API

## 🔒 Segurança

O endpoint de seed requer autenticação via API Key para prevenir:
- Execução não autorizada de operações de banco
- Inserção de dados maliciosos
- Vazamento de informações via endpoint de status

Configure `ADMIN_API_KEY` no `.env` com valor seguro.

## ✅ Boas Práticas

- Sempre verifique idempotência
- Use transações para operações atômicas
- Log adequado de execuções
- Tratamento de erros robusto
