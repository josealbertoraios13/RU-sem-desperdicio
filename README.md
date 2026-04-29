# Smart RU
## RU <span style="color: green;">Sem</span> Disperdício
### Sistema inteligente para reduzir desperdício de alimentos

<span style="font-weight: bolder;">Aplicação:</span> Sistemas de Informação aplicados à gestão do <span style="font-weight: bolder;">Restaurante Universitário da UFRPE </span>com foco em sustentabilidade

## Contribuição:
<ol>
    <li>Reduz desperdício de comida</li>
    <li>Ajuda no planejamento de refeições</li>
    <li>Facilita a organização dos estudantes e convidados</li>
</ol>

## Funcionalidades principais (release 1.0)
<ol>
    <li>Cadastro e Login </li>
    <li>Agendamento de Almoço e Jantar</li>
    <li>Cancelamento e Reagendamento</li>
    <li>Contativo de agendamentos no dia</li>li
</ol>

Projeto interdisciplinar - Sistemas de Informação | Desenvolvido por Tomás Kavela e José Alberto

## Instalação:
Antes de qualquer instalação, você precisa saber o que já deve ter instalado (Python 3.11+, Git, Docker).

Clone o repositório com o seguinte comando:
```bash
git clone https://github.com/josealbertoraios13/RU-sem-desperdicio.git
```

### Antes de tudo crie um Ambiente Virtual
**Linux/MacOs**
```bash
python3 -m venv venv # Cria o ambiente

source venv/bin/activate # Ativa o ambiente

pip install --upgrade pip # Atualiza o pip
pip install -r requirements.txt # Instala dependências descritas no arquivo requirements.txt
```

**Windows**
```bash
python -m venv venv

.\venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

### Dependências (requirements.txt):

#### Core dependencies
<ol>
    <li>bcrypt==4.1.2</li>
    <li>pyfiglet==1.0.4</li>
    <li>windows-curses==2.3.3  # necessário apenas no Windows</li>
</ol>

#### PostgreSQL dependencies
<ol>
    <li>psycopg2-binary==2.9.9</li>
    <li>SQLAlchemy==2.0.29</li>
    <li>alembic==1.13.1</li>
    <li>python-dotenv==1.0.0</li>
</ol>

Para instalar as dependências automaticamente e ter um feedback dinâmico rode:
```bash
    python3 setup.py
```

### DockerFile

#### Contém informações de dependências

```bash
FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libncurses5-dev \
    libncursesw5-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências do python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cria um usuário que não é root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Define variáveis de ambiente
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Roda o programa
CMD ["python", "main.py"]
```

### Instalação do Docker

#### Windows e macOS:

A forma mais simples é baixar o Docker Desktop:

    Acesse o site oficial: docker.com/products/docker-desktop.

    Baixe e siga as instruções do instalador.

    No Windows, certifique-se de que o WSL2 está ativado.
    O Docker Desktop já inclui o Docker Compose por padrão.

### Linux (Ubuntu/Debian):

#### Execute os comandos no terminal:
```bash
# Atualize e instale dependências
sudo apt update
sudo apt install ca-certificates curl gnupg

# Adicione a chave GPG oficial
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Adicione o repositório do Docker (PASSO QUE FALTAVA)
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instale Docker + Compose
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### Depois de Instalar o Docker:
```bash
docker compose up -d
```
Ou se você estiver usando o Visual Studio Code, abra o arquivo docker-compose.yml e instale a extensão que será recomendada, volte para o código .yml e você verá um botão escrito: "Run all services" clique nele.

### Variáveis de Ambiente
#### Você deve criar um arquivo .env e adicionar

dotenv_exemplo:
```bash
# PostgreSQL Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your_db
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password

# Connection Pool Settings (for high volume >1000 users)
DB_POOL_MIN_CONNECTIONS=1
DB_POOL_MAX_CONNECTIONS=20
DB_POOL_TIMEOUT=30  # seconds
DB_POOL_RECYCLE=3600  # seconds (1 hour)

# Application Settings
APP_ENV=development  # development, testing, production
APP_DEBUG=True

# Security Settings
BCRYPT_ROUNDS=12
```

### App.log
#### Todas as mensagens de erro e debug são direcionadas para este arquivo

### Para rodar o projeto: 
```bash
python3 main.py
```
