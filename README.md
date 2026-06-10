# Smart RU
## RU Sem Desperdício
### Sistema inteligente para reduzir desperdício de alimentos

**Aplicação:** Sistemas de Informação aplicados à gestão do **Restaurante Universitário da UFRPE** com foco em sustentabilidade

## Contribuição

1. Reduz desperdício de comida
2. Ajuda no planejamento de refeições
3. Facilita a organização dos estudantes e convidados

## Funcionalidades (release 1.0)

1. Cadastro e Login
2. Agendamento de Almoço e Jantar
3. Cancelamento do agendamento
4. Contador de agendamentos no dia

## Funcionalidades (release 2.0) - Em desenvolvimento
1. Reagendamento
2. Limite de datas por semestres
3. Código da ficha
4. Válidar o código da ficha
5. Notificações para o usuário

## Funcionalidades (release 3.0) - A definir...

## Fluxogramas e planilhas

Google Drive: https://drive.google.com/drive/u/2/folders/18Q5JASMbqB5pS0edGiqd0IbVv-v5YY76

Projeto interdisciplinar - Sistemas de Informação | Desenvolvido por Tomás Kavela e José Alberto

---

## Instalação

Antes de qualquer instalação, certifique-se de ter instalado: **Python 3.11+**, **Git** e **Docker**.

Clone o repositório:

```bash
git clone https://github.com/josealbertoraios13/RU-sem-desperdicio.git
```

### Criando o Ambiente Virtual

**Linux/macOS**
```bash
python3 -m venv venv          # Cria o ambiente
source venv/bin/activate      # Ativa o ambiente
pip install --upgrade pip     # Atualiza o pip
pip install -r requirements.txt  # Instala as dependências
```

**Windows**
```bash
python -m venv venv
.\venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Dependências (`requirements.txt`)

#### Core
- `bcrypt==4.1.2`
- `pyfiglet==1.0.4`
- `windows-curses==2.3.3` *(necessário apenas no Windows) - (recomendamos utilizar o wsl)*

#### PostgreSQL
- `psycopg2-binary==2.9.9`
- `SQLAlchemy==2.0.29`
- `alembic==1.13.1`
- `python-dotenv==1.0.0`

Para instalar as dependências automaticamente com feedback dinâmico:

```bash
python3 setup.py
```

---

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libncurses5-dev \
    libncursesw5-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências do Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cria um usuário não-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Define variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Inicia o programa
CMD ["python", "main.py"]
```

---

### Instalação do Docker

#### Windows e macOS

Baixe o **Docker Desktop** em [docker.com/products/docker-desktop](https://docker.com/products/docker-desktop) e siga as instruções do instalador.

> **Windows:** certifique-se de que o **WSL2** está ativado. O Docker Desktop já inclui o Docker Compose.

#### Linux (Ubuntu/Debian)

```bash
# Atualize e instale dependências
sudo apt update
sudo apt install ca-certificates curl gnupg

# Adicione a chave GPG oficial
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Adicione o repositório do Docker
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instale Docker + Compose
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

---

### Subindo os serviços

```bash
docker compose up -d
```

> Ou, no **VS Code**, abra o `docker-compose.yml`, instale a extensão recomendada e clique em **"Run all services"**.

---

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your_db
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password

# Connection Pool (para alto volume, >1000 usuários)
DB_POOL_MIN_CONNECTIONS=1
DB_POOL_MAX_CONNECTIONS=20
DB_POOL_TIMEOUT=30       # segundos
DB_POOL_RECYCLE=3600     # segundos (1 hora)

# Aplicação
APP_ENV=development      # development, testing, production
APP_DEBUG=True

# Segurança
BCRYPT_ROUNDS=12
```

---

### Logs

Todas as mensagens de erro e debug são registradas no arquivo `app.log`.

---

### Rodando o projeto

```bash
python3 main.py
```
