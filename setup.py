#!/usr/bin/env python3
"""
Setup script for SmartRU PostgreSQL dependencies
"""

import os
import sys
import subprocess
import platform
import shutil
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# ─── Terminal colors ──────────────────────────────────────────────────────────

_USE_COLOR = sys.stdout.isatty()

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text

ok   = lambda t: print(_c("32", f"  ✓ {t}"))
warn = lambda t: print(_c("33", f"  ⚠ {t}"))
err  = lambda t: print(_c("31", f"  ✗ {t}"))
info = lambda t: print(f"  {t}")

def section(title: str) -> None:
    print(f"\n{_c('1;34', title)}")
    print(_c("34", "─" * 50))


# ─── Result tracking ──────────────────────────────────────────────────────────

@dataclass
class SetupResult:
    name: str
    passed: bool
    detail: Optional[str] = None


@dataclass
class SetupReport:
    results: list[SetupResult] = field(default_factory=list)

    def add(self, name: str, passed: bool, detail: str = None) -> bool:
        self.results.append(SetupResult(name, passed, detail))
        return passed

    def print_summary(self) -> None:
        section("Summary")
        for r in self.results:
            label = _c("32", "PASS") if r.passed else _c("31", "FAIL")
            detail = f"  → {r.detail}" if r.detail else ""
            print(f"  [{label}] {r.name}{detail}")
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        color = "32" if passed == total else "31" if passed < total // 2 else "33"
        print(f"\n  {_c(color, f'{passed}/{total} checks passed')}")

    @property
    def all_passed(self) -> bool:
        return all(r.passed for r in self.results)


# ─── Checks ───────────────────────────────────────────────────────────────────

def check_python_version(report: SetupReport) -> bool:
    section("Python")
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    info(f"Python {version_str}")

    if v < (3, 8):
        err(f"Python 3.8+ required, got {version_str}")
        return report.add("Python version", False, version_str)

    ok(f"Python {version_str}")
    return report.add("Python version", True)


def check_pip(report: SetupReport) -> bool:
    section("pip")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True, text=True, check=True,
        )
        ok(result.stdout.strip())
        return report.add("pip available", True)
    except subprocess.CalledProcessError:
        err("pip not found")
        return report.add("pip available", False, "install pip manually")


def install_dependencies(report: SetupReport) -> bool:
    section("Dependencies")
    req_file = Path("requirements.txt")

    if not req_file.exists():
        err("requirements.txt not found")
        return report.add("Install dependencies", False, "requirements.txt missing")

    info(f"Installing from {req_file} …")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
        capture_output=True, text=True,
    )

    if result.returncode == 0:
        ok("All packages installed")
        return report.add("Install dependencies", True)

    err("pip install failed")
    for line in result.stderr.splitlines()[-10:]:   # last 10 lines of stderr
        info(f"  {line}")
    return report.add("Install dependencies", False, "see errors above")


def check_required_packages(report: SetupReport) -> bool:
    """Verify critical imports are resolvable after install."""
    section("Package imports")
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
            err(f"{module}  (install '{pkg}')")
            all_ok = False

    return report.add("Required packages", all_ok,
                       None if all_ok else "run: pip install psycopg2-binary python-dotenv")


def setup_environment(report: SetupReport) -> bool:
    section("Environment (.env)")
    env_path = Path(".env")

    if not env_path.exists():
        example = Path(".env.example")
        if example.exists():
            shutil.copy2(example, env_path)
            ok(".env created from .env.example")
            warn("Edit .env with your database credentials before continuing")
        else:
            warn(".env.example not found — creating minimal .env")
            env_path.write_text(
                "# PostgreSQL Configuration\n"
                "POSTGRES_HOST=localhost\n"
                "POSTGRES_PORT=5432\n"
                "POSTGRES_DB=smartru_db\n"
                "POSTGRES_USER=smartru_user\n"
                "POSTGRES_PASSWORD=smartru_password\n"
            )
            ok(".env created")
    else:
        ok(".env already exists")

    # Validate required keys are present and non-empty
    required_keys = ["POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB",
                     "POSTGRES_USER", "POSTGRES_PASSWORD"]
    env_vars = _parse_env_file(env_path)
    missing = [k for k in required_keys if not env_vars.get(k)]

    if missing:
        warn(f"Missing or empty keys in .env: {', '.join(missing)}")
        return report.add("Environment config", False, f"fill in: {', '.join(missing)}")

    ok("All required .env keys are set")
    return report.add("Environment config", True)


def _parse_env_file(path: Path) -> dict:
    """Parse KEY=VALUE lines from a .env file, ignoring comments."""
    env: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def check_system_dependencies(report: SetupReport) -> bool:
    section("System dependencies")
    system = platform.system().lower()
    info(f"Platform: {platform.system()} {platform.machine()}")

    hints = {
        "linux":  "sudo apt-get install libncurses5-dev libncursesw5-dev",
        "darwin": "brew install ncurses",
        "windows": "Consider using WSL2 for full curses support",
    }

    if system in hints:
        warn(f"curses may need: {hints[system]}")
    else:
        warn("Check your OS docs for ncurses installation")

    # Verify libpq (postgres client library) is available
    libpq_found = shutil.which("pg_config") is not None
    if libpq_found:
        ok("pg_config found (libpq available)")
    else:
        warn("pg_config not found — libpq may be missing")
        if system == "linux":
            info("    sudo apt-get install libpq-dev")
        elif system == "darwin":
            info("    brew install libpq")

    return report.add("System deps (ncurses/libpq hint)", True)   # advisory only


def test_postgres_connection(report: SetupReport) -> bool:
    section("PostgreSQL connection")

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        warn("python-dotenv not installed — reading env vars from OS environment only")

    sys.path.insert(0, str(Path(__file__).parent.resolve()))

    try:
        from database import DataBase  # type: ignore
        ok("database module imported")
    except ImportError as e:
        err(f"Cannot import 'database' module: {e}")
        return report.add("PostgreSQL connection", False, "database.py not found in project")

    try:
        db = DataBase()
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        row = cursor.fetchone()
        pg_version = row[0].split(",")[0] if row else "unknown"
        ok(f"Connected — {pg_version}")
        db.connection_pool.putconn(conn)
        db.close()
        return report.add("PostgreSQL connection", True, pg_version)
    except Exception as e:
        err(f"Connection failed: {e}")
        info("Troubleshooting:")
        info("  1. Is PostgreSQL running?  (systemctl status postgresql)")
        info("  2. Are the .env credentials correct?")
        info("  3. Does the user have CONNECT privilege on the database?")
        return report.add("PostgreSQL connection", False, str(e))


# ─── CLI ─────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="SmartRU PostgreSQL setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python setup.py              # interactive\n"
            "  python setup.py --yes        # install everything non-interactively\n"
            "  python setup.py --skip-install --test  # only test the DB connection\n"
            "  python setup.py --check      # dry-run (no install, no DB test)\n"
        ),
    )
    p.add_argument("--yes",          "-y", action="store_true",
                   help="Non-interactive: assume yes to all prompts")
    p.add_argument("--skip-install",       action="store_true",
                   help="Skip pip dependency installation")
    p.add_argument("--test",               action="store_true",
                   help="Always run the PostgreSQL connection test")
    p.add_argument("--no-test",            action="store_true",
                   help="Never run the PostgreSQL connection test")
    p.add_argument("--check",              action="store_true",
                   help="Dry-run: only check prerequisites, no installs or DB tests")
    return p.parse_args()


def ask(prompt: str, *, default_yes: bool = False) -> bool:
    hint = "(Y/n)" if default_yes else "(y/N)"
    answer = input(f"\n{prompt} {hint}: ").strip().lower()
    if not answer:
        return default_yes
    return answer in ("y", "yes")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> bool:
    args = parse_args()

    print(_c("1", "\n" + "=" * 52))
    print(_c("1", "  SmartRU PostgreSQL Setup"))
    print(_c("1", "=" * 52))

    report = SetupReport()

    # Prerequisites (always run)
    check_python_version(report)
    check_pip(report)
    check_system_dependencies(report)
    setup_environment(report)

    if args.check:
        info("\n--check mode: skipping installs and DB test")
        report.print_summary()
        return report.all_passed

    # Install dependencies
    do_install = (
        not args.skip_install
        and (args.yes or ask("Install Python dependencies?", default_yes=True))
    )
    if do_install:
        install_dependencies(report)
        check_required_packages(report)
    else:
        info("\nSkipping dependency installation")
        check_required_packages(report)   # still verify what's already installed

    # PostgreSQL connection test
    if args.no_test:
        info("\nSkipping PostgreSQL connection test (--no-test)")
    else:
        do_test = args.test or args.yes or ask("Test PostgreSQL connection?")
        if do_test:
            test_postgres_connection(report)

    report.print_summary()

    if report.all_passed:
        print(_c("32", "\n✅ Setup complete!\n"))
        print("Next steps:")
        print("  python main.py          # run the application")
        print("  docker-compose up       # or use Docker")
    else:
        print(_c("33", "\n⚠  Setup finished with issues — see summary above\n"))

    return report.all_passed


if __name__ == "__main__":
    try:
        sys.exit(0 if main() else 1)
    except KeyboardInterrupt:
        print(_c("33", "\n\nSetup interrupted by user"))
        sys.exit(130)