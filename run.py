"""Start the SATYA backend and frontend together.

Usage:
    python run.py
    python run.py --skip-install

The launcher intentionally does not print or modify secret values. It creates
local .env files from the committed examples only when they do not exist.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
BACKEND_HOST = "localhost"
BACKEND_PORT = 8000
FRONTEND_HOST = "localhost"
FRONTEND_PORT = 5173


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


def command_succeeds(command: list[str], cwd: Path) -> bool:
    return subprocess.run(command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def install_dependencies() -> None:
    backend_python = python_executable()
    backend_ready = command_succeeds(
        [backend_python, "-c", "import fastapi, httpx, pydantic_settings, supabase"],
        BACKEND,
    )
    if not backend_ready:
        run_checked([backend_python, "-m", "pip", "install", "-r", "requirements.txt"], BACKEND)
    else:
        print("Backend dependencies are already installed; skipping pip install.")

    if not (FRONTEND / "node_modules").exists():
        npm = "npm.cmd" if os.name == "nt" else "npm"
        run_checked([npm, "install"], FRONTEND)
    else:
        print("Frontend dependencies are already installed; skipping npm install.")


def check_tools() -> None:
    if not shutil.which("node"):
        raise RuntimeError("Node.js is required to start the frontend. Install Node.js and run python run.py again.")
    if not shutil.which("npm") and not shutil.which("npm.cmd"):
        raise RuntimeError("npm is required to start the frontend. Install Node.js and run python run.py again.")


def check_univfd_runtime() -> None:
    """Fail before startup if the configured image inference runtime is unusable."""
    backend_python = python_executable()
    check = (
        "import os, pathlib, torch; "
        "from PIL import Image; "
        "from app.model_registry import predict; "
        "checkpoint = pathlib.Path(os.environ.get("
        "'SATYA_UNIVFD_CHECKPOINT', "
        "str(pathlib.Path('models') / 'image' / 'fc_weights.pth'))); "
        "assert torch.cuda.is_available(), "
        "'CUDA is unavailable; UnivFD image inference requires CUDA'; "
        "assert checkpoint.is_file(), f'UnivFD checkpoint not found: {checkpoint}'; "
        "print(f'CUDA device: {torch.cuda.get_device_name(0)}'); "
        "print(f'UnivFD checkpoint: {checkpoint.resolve()}')"
    )
    try:
        result = subprocess.run(
            [backend_python, "-c", check],
            cwd=BACKEND,
            env=os.environ.copy(),
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout).strip()
        raise RuntimeError(
            "UnivFD runtime check failed. Verify CUDA, PyTorch, Pillow, and "
            f"the classifier checkpoint. {detail}"
        ) from error
    print(result.stdout.strip())


def report_configuration() -> None:
    frontend_env = FRONTEND / ".env"
    if not frontend_env.exists():
        return
    values = {}
    for line in frontend_env.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    if values.get("VITE_SUPABASE_URL") in {"", "https://your-project.supabase.co"} or values.get("VITE_SUPABASE_ANON_KEY") in {"", "your-anon-key"}:
        print(
            "Warning: frontend/.env still has placeholder Supabase values. "
            "The app will start, but sign-up/sign-in will not work until you replace them."
        )


def backend_is_satya() -> bool:
    health_url = f"http://{BACKEND_HOST}:{BACKEND_PORT}/api/health"
    openapi_url = f"http://{BACKEND_HOST}:{BACKEND_PORT}/openapi.json"
    try:
        with urllib.request.urlopen(health_url, timeout=2) as response:
            if response.status != 200:
                return False
            health = json.loads(response.read().decode("utf-8"))
        with urllib.request.urlopen(openapi_url, timeout=2) as response:
            if response.status != 200:
                return False
            specification = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError):
        return False

    info = specification.get("info", {})
    paths = specification.get("paths", {})
    return (
        health.get("status") == "ok"
        and health.get("service") == "satya"
        and info.get("title") == "SATYA"
        and info.get("version") == "0.1.0"
        and "/api/health" in paths
        and "/api/upload" in paths
    )


def backend_port_is_available() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        try:
            probe.bind(("127.0.0.1", BACKEND_PORT))
        except OSError:
            return False
    return True


def resolve_backend() -> subprocess.Popen[str] | None:
    if backend_is_satya():
        print(
            f"Verified existing SATYA backend at "
            f"http://{BACKEND_HOST}:{BACKEND_PORT}; reusing it."
        )
        return None
    if not backend_port_is_available():
        raise RuntimeError(
            f"Port {BACKEND_PORT} is occupied, but the server did not identify "
            "itself as SATYA. No process was terminated. Stop the owning service "
            "or free the port, then run python run.py again."
        )
    backend_python = python_executable()
    process = subprocess.Popen(
        [
            backend_python,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            BACKEND_HOST,
            "--port",
            str(BACKEND_PORT),
        ],
        cwd=BACKEND,
        env=os.environ.copy(),
        text=True,
    )
    wait_for_backend(process)
    return process


def wait_for_backend(process: subprocess.Popen[str]) -> None:
    deadline = time.time() + 60
    url = f"http://{BACKEND_HOST}:{BACKEND_PORT}/api/health"
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError("The backend stopped during startup.")
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)
    raise RuntimeError(
        f"The backend did not become ready at http://{BACKEND_HOST}:{BACKEND_PORT} within 60 seconds."
    )


def start_frontend() -> subprocess.Popen[str]:
    frontend_environment = os.environ.copy()
    frontend_environment["VITE_API_BASE_URL"] = "http://127.0.0.1:8000"
    return subprocess.Popen(
        [
            shutil.which("node") or "node",
            str(FRONTEND / "node_modules" / "vite" / "bin" / "vite.js"),
            "--host",
            FRONTEND_HOST,
            "--port",
            str(FRONTEND_PORT),
        ],
        cwd=FRONTEND,
        env=frontend_environment,
        text=True,
    )


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
    check_tools()
    report_configuration()

    if not args.skip_install:
        install_dependencies()

    if not backend_is_satya():
        check_univfd_runtime()
    try:
        backend_process = resolve_backend()
        if not backend_port_is_available() and backend_process is None:
            pass
        if not backend_process and not backend_is_satya():
            raise RuntimeError("SATYA backend verification changed during startup.")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.5)
            probe.bind(("127.0.0.1", FRONTEND_PORT))
        frontend_process = start_frontend()
    except (OSError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    processes = [process for process in (backend_process, frontend_process) if process is not None]
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
