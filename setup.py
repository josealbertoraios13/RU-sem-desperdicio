
import sys  # Importa parâmetros e funções específicas do sistema
import subprocess  # Permite a execução de comandos externos
import platform  # Acessa dados de identificação da plataforma/SO
import shutil  # Fornece operações de arquivo de alto nível (como copiar)
import argparse  # Facilita a criação de interfaces de linha de comando
from pathlib import Path  # Manipula caminhos de arquivos de forma orientada a objetos
from dataclasses import dataclass, field  # Facilita a criação de classes de dados
from typing import Optional  # Usado para indicações de tipos opcionais


# Verifica se a saída padrão é um terminal interativo para habilitar cores
_USE_COLOR = sys.stdout.isatty()

# Função auxiliar para aplicar códigos de cores ANSI ao texto
def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text

# Atalhos para mensagens coloridas: Verde (sucesso), Amarelo (aviso), Vermelho (erro), Azul (info)
ok   = lambda t: print(_c("32", f"  ✓ {t}"))
warn = lambda t: print(_c("33", f"  ⚠ {t}"))
err  = lambda t: print(_c("31", f"  ✗ {t}"))
info = lambda t: print(f"  {t}")

# Imprime um título de seção estilizado
def section(title: str) -> None:
    print(f"\n{_c('1;34', title)}")
    print(_c("34", "─" * 50))


@dataclass
class SetupResult:  # Armazena o resultado de uma verificação individual
    name: str  # Nome do teste
    passed: bool  # Se passou ou não
    detail: Optional[str] = None  # Detalhes adicionais (opcional)


@dataclass
class SetupReport:  # Agrega todos os resultados do processo
    results: list[SetupResult] = field(default_factory=list)

    # Adiciona um novo resultado à lista e retorna o status booleano
    def add(self, name: str, passed: bool, detail: str = None) -> bool:
        self.results.append(SetupResult(name, passed, detail))
        return passed

    # Exibe o resumo final formatado no terminal
    def print_summary(self) -> None:
        section("Resumo")
        for r in self.results:
            label = _c("32", "PASSOU") if r.passed else _c("31", "FALHOU")
            detail = f"  → {r.detail}" if r.detail else ""
            print(f"  [{label}] {r.name}{detail}")
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        # Define a cor do placar final com base no desempenho
        color = "32" if passed == total else "31" if passed < total // 2 else "33"
        print(f"\n  {_c(color, f'{passed}/{total} verificações concluídas')}")

    @property
    def all_passed(self) -> bool:  # Verifica se tudo passou sem erros
        return all(r.passed for r in self.results)


def check_python_version(report: SetupReport) -> bool:
    section("Python")
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    info(f"Versão detectada: {version_str}")

    # Garante que a versão seja pelo menos 3.8
    if v < (3, 8):
        err(f"Python 3.8+ é necessário, você tem {version_str}")
        return report.add("Versão do Python", False, version_str)

    ok(f"Python {version_str}")
    return report.add("Versão do Python", True)


def check_pip(report: SetupReport) -> bool:
    section("pip")
    try:
        # Tenta executar o comando pip para ver se ele existe
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True, text=True, check=True,
        )
        ok(result.stdout.strip())
        return report.add("pip disponível", True)
    except subprocess.CalledProcessError:
        err("pip não encontrado")
        return report.add("pip disponível", False, "instale o pip manualmente")


def install_dependencies(report: SetupReport) -> bool:
    section("Dependências")
    req_file = Path("requirements.txt")

    # Verifica a existência do arquivo de requisitos
    if not req_file.exists():
        err("requirements.txt não encontrado")
        return report.add("Instalar dependências", False, "arquivo ausente")

    info(f"Instalando pacotes via {req_file} …")
    # Executa a instalação silenciosa via pip
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
        capture_output=True, text=True,
    )

    if result.returncode == 0:
        ok("Todos os pacotes foram instalados")
        return report.add("Instalar dependências", True)

    # Em caso de erro, exibe as últimas 10 linhas do erro gerado
    err("Falha na instalação via pip")
    for line in result.stderr.splitlines()[-10:]:
        info(f"  {line}")
    return report.add("Instalar dependências", False, "verifique os erros acima")


def check_required_packages(report: SetupReport) -> bool:
    # Valida se os módulos críticos podem ser importados após a instalação
    section("Importação de pacotes")
    packages = {
        "psycopg2": "psycopg2-binary",
        "dotenv":   "python-dotenv",
    }
    all_ok = True
    for module, pkg in packages.items():
        result = subprocess.run(
            [sys.executable, "-c", f"import {module}"],
            capture_output=True,
        )
        if result.returncode == 0:
            ok(f"{module}")
        else:
            err(f"{module}  (instale '{pkg}')")
            all_ok = False

    return report.add("Pacotes obrigatórios", all_ok,
                       None if all_ok else "execute: pip install psycopg2-binary python-dotenv")


def setup_environment(report: SetupReport) -> bool:
    section("Ambiente (.env)")
    env_path = Path(".env")

    # Lógica de criação do arquivo de ambiente se ele não existir
    if not env_path.exists():
        example = Path(".env.example")
        if example.exists():
            shutil.copy2(example, env_path)
            ok(".env criado a partir de .env.example")
            warn("Edite o .env com suas credenciais do banco de dados")
        else:
            warn(".env.example não encontrado — criando .env mínimo")
            env_path.write_text(
                "# Configuração PostgreSQL\n"
                "POSTGRES_HOST=localhost\n"
                "POSTGRES_PORT=5432\n"
                "POSTGRES_DB=smartru_db\n"
                "POSTGRES_USER=smartru_user\n"
                "POSTGRES_PASSWORD=smartru_password\n"
            )
            ok(".env criado")
    else:
        ok(".env já existe")

    # Lista de chaves obrigatórias que devem estar preenchidas
    required_keys = ["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB",
                     "POSTGRES_USER", "POSTGRES_PASSWORD"]
    env_vars = _parse_env_file(env_path)
    missing = [k for k in required_keys if not env_vars.get(k)]

    # Se houver chaves vazias ou ausentes, avisa o usuário
    if missing:
        warn(f"Chaves ausentes ou vazias no .env: {', '.join(missing)}")
        return report.add("Configuração de ambiente", False, f"preencher: {', '.join(missing)}")

    ok("Todas as chaves obrigatórias do .env estão definidas")
    return report.add("Configuração de ambiente", True)


def _parse_env_file(path: Path) -> dict:
    # Função interna para ler o arquivo .env e transformar em dicionário Python
    env: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        # Pula linhas vazias, comentários ou linhas sem o sinal de igual
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        # Remove espaços e aspas extras dos valores
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def check_system_dependencies(report: SetupReport) -> bool:
    section("Dependências do sistema")
    system = platform.system().lower()
    info(f"Plataforma: {platform.system()} {platform.machine()}")

    # Dicas de comandos de instalação baseados no Sistema Operacional
    hints = {
        "linux":  "sudo apt-get install libncurses5-dev libncursesw5-dev",
        "darwin": "brew install ncurses",
        "windows": "Considere usar WSL2 para suporte completo ao curses",
    }

    if system in hints:
        warn(f"O curses pode precisar de: {hints[system]}")
    else:
        warn("Verifique a documentação do seu SO para instalar o ncurses")

    # Tenta localizar o binário pg_config, essencial para bibliotecas de conexão Postgres
    libpq_found = shutil.which("pg_config") is not None
    if libpq_found:
        ok("pg_config encontrado (libpq disponível)")
    else:
        warn("pg_config não encontrado — libpq pode estar ausente")
        if system == "linux":
            info("    sudo apt-get install libpq-dev")
        elif system == "darwin":
            info("    brew install libpq")

    return report.add("Dependências do sistema (dicas)", True)


def test_postgres_connection(report: SetupReport) -> bool:
    section("Conexão PostgreSQL")

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        warn("python-dotenv não instalado — lendo variáveis apenas do ambiente do SO")

    # Adiciona o diretório atual ao path para garantir que o módulo local seja encontrado
    sys.path.insert(0, str(Path(__file__).parent.resolve()))

    try:
        from database import DataBase  # tenta carregar a classe de banco de dados do projeto
        ok("Módulo database importado")
    except ImportError as e:
        err(f"Não foi possível importar o módulo 'database': {e}")
        return report.add("Conexão PostgreSQL", False, "database.py não encontrado")

    try:
        # Instancia a classe, conecta, executa uma query de versão e fecha
        db = DataBase()
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        row = cursor.fetchone()
        pg_version = row[0].split(",")[0] if row else "desconhecida"
        ok(f"Conectado — {pg_version}")
        db.connection_pool.putconn(conn)
        db.close()
        return report.add("Conexão PostgreSQL", True, pg_version)
    except Exception as e:
        err(f"Conexão falhou: {e}")
        info("Dicas para solução:")
        info("  1. O PostgreSQL está rodando? (systemctl status postgresql)")
        info("  2. As credenciais no .env estão corretas?")
        info("  3. O usuário tem privilégio de CONNECT no banco?")
        return report.add("Conexão PostgreSQL", False, str(e))


def parse_args() -> argparse.Namespace:
    # Configura os argumentos aceitos pela linha de comando
    p = argparse.ArgumentParser(
        description="Configuração SmartRU PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  python setup.py              # modo interativo\n"
            "  python setup.py --yes        # instala tudo sem perguntar\n"
            "  python setup.py --skip-install --test  # apenas testa a conexão\n"
            "  python setup.py --check      # apenas verifica pré-requisitos\n"
        ),
    )
    p.add_argument("--yes",          "-y", action="store_true",
                   help="Não interativo: assume 'sim' para tudo")
    p.add_argument("--skip-install",       action="store_true",
                   help="Pula a instalação de dependências do pip")
    p.add_argument("--test",               action="store_true",
                   help="Sempre executa o teste de conexão com o banco")
    p.add_argument("--no-test",            action="store_true",
                   help="Nunca executa o teste de conexão")
    p.add_argument("--check",              action="store_true",
                   help="Apenas verifica requisitos, sem instalar ou testar banco")
    return p.parse_args()


def ask(prompt: str, *, default_yes: bool = False) -> bool:
    # Função para fazer perguntas sim/não ao usuário no terminal
    hint = "(S/n)" if default_yes else "(s/N)"
    answer = input(f"\n{prompt} {hint}: ").strip().lower()
    if not answer:
        return default_yes
    return answer in ("s", "sim", "y", "yes")


def main() -> bool:
    args = parse_args()

    # Cabeçalho decorativo
    print(_c("1", "\n" + "=" * 52))
    print(_c("1", "  Configuração SmartRU PostgreSQL"))
    print(_c("1", "=" * 52))

    report = SetupReport()

    # Executa verificações básicas iniciais
    check_python_version(report)
    check_pip(report)
    check_system_dependencies(report)
    setup_environment(report)

    if args.check:
        info("\nModo --check: pulando instalações e testes de banco")
        report.print_summary()
        return report.all_passed

    # Decide se deve instalar dependências baseado em argumentos ou interação
    do_install = (
        not args.skip_install
        and (args.yes or ask("Instalar dependências do Python?", default_yes=True))
    )
    if do_install:
        install_dependencies(report)
        check_required_packages(report)
    else:
        info("\nPulando instalação de dependências")
        check_required_packages(report)

    # Decide se deve testar a conexão com o banco de dados
    if args.no_test:
        info("\nPulando teste de conexão PostgreSQL (--no-test)")
    else:
        do_test = args.test or args.yes or ask("Testar conexão com o PostgreSQL?")
        if do_test:
            test_postgres_connection(report)

    report.print_summary()

    # Mensagem final baseada no sucesso global
    if report.all_passed:
        print(_c("32", "\n✅ Configuração concluída!\n"))
        print("Próximos passos:")
        print("  python main.py          # executa a aplicação")
        print("  docker-compose up       # ou use o Docker")
    else:
        print(_c("33", "\n⚠  Configuração finalizada com problemas — veja o resumo acima\n"))

    return report.all_passed


if __name__ == "__main__":
    try:
        # Sai com código 0 se sucesso, 1 se erro
        sys.exit(0 if main() else 1)
    except KeyboardInterrupt:
        # Trata interrupção via Ctrl+C graciosamente
        print(_c("33", "\n\nConfiguração interrompida pelo usuário"))
        sys.exit(130)