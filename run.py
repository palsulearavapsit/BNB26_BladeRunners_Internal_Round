"""Start the SATYA backend and frontend together.

Usage:
    python run.py
    python run.py --skip-install

The launcher intentionally does not print or modify secret values. It creates
local .env files from the committed examples only when they do not exist.
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def copy_env_if_missing(directory: Path) -> None:
    env_file = directory / ".env"
    example = directory / ".env.example"
    if not env_file.exists() and example.exists():
        shutil.copyfile(example, env_file)
        print(f"Created {env_file.relative_to(ROOT)} from .env.example")


def run_checked(command: list[str], cwd: Path) -> None:
    print(f"Running: {' '.join(command)}")
    subprocess.run(command, cwd=cwd, check=True)


def python_executable() -> str:
    candidates = [
        BACKEND / ".venv" / "Scripts" / "python.exe",
        BACKEND / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def install_dependencies() -> None:
    backend_python = python_executable()
    run_checked([backend_python, "-m", "pip", "install", "-r", "requirements.txt"], BACKEND)
    if not (FRONTEND / "node_modules").exists():
        npm = "npm.cmd" if os.name == "nt" else "npm"
        run_checked([npm, "install"], FRONTEND)


def start_processes() -> list[subprocess.Popen[str]]:
    backend_python = python_executable()
    npm = "npm.cmd" if os.name == "nt" else "npm"
    backend = subprocess.Popen(
        [backend_python, "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BACKEND,
        env=os.environ.copy(),
        text=True,
    )
    frontend = subprocess.Popen(
        [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
        cwd=FRONTEND,
        env=os.environ.copy(),
        text=True,
    )
    return [backend, frontend]


def stop_processes(processes: list[subprocess.Popen[str]]) -> None:
    for process in processes:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
    deadline = time.time() + 5
    while time.time() < deadline and any(process.poll() is None for process in processes):
        time.sleep(0.1)
    for process in processes:
        if process.poll() is None:
            process.kill()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the SATYA backend and frontend")
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Do not install Python or frontend dependencies before starting",
    )
    args = parser.parse_args()

    if not BACKEND.exists() or not FRONTEND.exists():
        print("SATYA requires both backend and frontend directories.", file=sys.stderr)
        return 1

    copy_env_if_missing(BACKEND)
    copy_env_if_missing(FRONTEND)

    if not args.skip_install:
        install_dependencies()

    processes = start_processes()
    print("\nSATYA is running:")
    print("  Frontend: http://localhost:5173")
    print("  Backend:  http://localhost:8000")
    print("  API docs: http://localhost:8000/docs")
    print("Press Ctrl+C to stop both services.\n")

    try:
        while True:
            if any(process.poll() is not None for process in processes):
                return 1
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping SATYA...")
        return 0
    finally:
        stop_processes(processes)


if __name__ == "__main__":
    raise SystemExit(main())
