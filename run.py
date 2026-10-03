"""Prepare and launch the stock dashboard. Run with: python run.py"""

from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import venv
import webbrowser


PROJECT_DIR = Path(__file__).resolve().parent
VENV_DIR = PROJECT_DIR / "venv"
APP_URL = "http://127.0.0.1:8501"


def venv_python() -> Path:
    """Create the project virtual environment if it does not exist."""
    python = VENV_DIR / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not python.exists():
        print("Creating virtual environment...")
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)
    return python


def install_missing_dependencies(python: Path) -> None:
    requirements = PROJECT_DIR / "requirements.txt"
    missing = []
    for line in requirements.read_text(encoding="utf-8").splitlines():
        package = line.partition("#")[0].strip()
        if package:
            result = subprocess.run(
                [str(python), "-m", "pip", "show", package],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if result.returncode:
                missing.append(package)

    if missing:
        print("Installing project dependencies...")
        subprocess.run(
            [str(python), "-m", "pip", "install", "-r", str(requirements)],
            cwd=PROJECT_DIR,
            check=True,
        )


def wait_for_server(process: subprocess.Popen) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Streamlit stopped before the dashboard became available.")
        try:
            with urllib.request.urlopen(APP_URL, timeout=1):
                return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.5)
    raise RuntimeError(f"Dashboard did not become available at {APP_URL}.")


def main() -> int:
    python = venv_python()
    install_missing_dependencies(python)

    env_file = PROJECT_DIR / ".env"
    example_env = PROJECT_DIR / ".env.example"
    if not env_file.exists() and example_env.exists():
        shutil.copyfile(example_env, env_file)

    command = [
        str(python), "-m", "streamlit", "run", "dashboard.py",
        "--server.headless", "true",
        "--server.address", "127.0.0.1",
        "--server.port", "8501",
    ]
    print("Starting the dashboard...")
    process = subprocess.Popen(command, cwd=PROJECT_DIR)

    try:
        wait_for_server(process)
        print(f"Dashboard ready at {APP_URL}")
        try:
            webbrowser.get("chrome").open_new_tab(APP_URL)
        except webbrowser.Error:
            webbrowser.open_new_tab(APP_URL)
        return process.wait()
    except KeyboardInterrupt:
        return 0
    except Exception as error:
        print(f"Could not start the dashboard: {error}", file=sys.stderr)
        return 1
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait()


if __name__ == "__main__":
    raise SystemExit(main())