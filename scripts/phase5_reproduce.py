"""Reproduce installation and acceptance outside the user's runtime storage.

Retains the disposable workspace for browser checks. Only sanitized command
output and version information are copied back as development evidence.
"""
from __future__ import annotations

import hashlib
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "ai_evidence" / "phase5"


def runtime_fingerprints():
    return {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (ROOT / "instance").glob("*.sqlite3")
    }


def main():
    global EVIDENCE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", default="ai_evidence/phase5",
                        help="Project-relative output folder; use a new folder to preserve prior runs.")
    args = parser.parse_args()
    requested = (ROOT / args.evidence_dir).resolve()
    if not requested.is_relative_to((ROOT / "ai_evidence").resolve()):
        parser.error("Evidence must be written inside the project's ai_evidence folder")
    EVIDENCE = requested
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    before = runtime_fingerprints()
    clean = Path(tempfile.mkdtemp(prefix="dorm-phase5-")) / "project"
    clean.mkdir()
    for name in ("app", "tests", "scripts", "docs"):
        if (ROOT / name).is_dir():
            shutil.copytree(ROOT / name, clean / name,
                            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc"))
    for name in ("run.py", "requirements.txt", "requirements-dev.txt", "README.md",
                 "DESIGN.md", "AGENTS.md", "PLANS.md", ".env.example", ".gitignore"):
        shutil.copy2(ROOT / name, clean / name)
    (ROOT / "instance").mkdir(exist_ok=True)
    (ROOT / "instance" / "phase5_workspace.txt").write_text(str(clean), encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if not k.startswith("DORM_REPAIR_")}
    env.update(PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    password = secrets.token_urlsafe(20)
    python = clean / ".venv" / "Scripts" / "python.exe"

    def run(label, args, *, stdin=None):
        print(f"START {label}", flush=True)
        try:
            result = subprocess.run(args, cwd=clean, env=env, input=stdin,
                                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                                    timeout=900 if label in {"install", "pytest"} else 120)
        except subprocess.TimeoutExpired:
            (EVIDENCE / f"{label}.txt").write_text("TIMEOUT: command did not finish within its limit\n", encoding="utf-8")
            raise
        output = (result.stdout + result.stderr).replace(password, "<redacted>")
        output = output.replace(str(clean), "<clean-workspace>").replace(str(ROOT), "<source-workspace>")
        output = re.sub(r"C:[\\/]+Users[\\/]+[^\\/\r\n]+", "<user-home>", output)
        output = re.sub(r"(https?://)[^/\s:@]+:[^/\s@]+@", r"\1<redacted>@", output)
        (EVIDENCE / f"{label}.txt").write_text(output, encoding="utf-8")
        print(f"END {label} exit={result.returncode}\n{output[-700:]}", flush=True)
        if result.returncode:
            raise RuntimeError(f"{label} failed; see sanitized evidence")
        return output

    run("venv", [sys._base_executable, "-m", "venv", str(clean / ".venv")])
    run("install", [str(python), "-m", "pip", "install", "--no-cache-dir",
                    "--disable-pip-version-check", "-r", "requirements-dev.txt"])
    run("pip_check", [str(python), "-m", "pip", "check"])
    run("versions", [str(python), "-c",
        "import sys,sqlite3,importlib.metadata as m,json;print(json.dumps({'python':sys.version.split()[0],"
        "'sqlite':sqlite3.sqlite_version,'packages':{d.metadata['Name']:d.version for d in m.distributions()}},indent=2))"])
    run("init", [str(python), "-m", "flask", "--app", "run:app", "init-db"])
    # Click's Windows hidden prompt may read from the console instead of a pipe.
    # Use the application's existing explicit non-interactive password input.
    env["DORM_REPAIR_DEMO_PASSWORD"] = password
    run("seed", [str(python), "-m", "flask", "--app", "run:app", "seed-demo"])
    run("init_repeat", [str(python), "-m", "flask", "--app", "run:app", "init-db"])
    run("seed_repeat", [str(python), "-m", "flask", "--app", "run:app", "seed-demo"])
    env.pop("DORM_REPAIR_DEMO_PASSWORD")
    run("pytest", [str(python), "-m", "pytest", "-q"])
    run("http_restart", [str(python), "scripts/phase4_http_smoke.py"])
    run("http_independent", [str(python), "scripts/phase5_http_acceptance.py"])
    run("http_categories", [str(python), "scripts/category_http_smoke.py"])
    after = runtime_fingerprints()
    assert before == after, "Source runtime database changed during reproduction"
    (EVIDENCE / "reproduction.json").write_text(json.dumps({
        "fresh_directory": True, "fresh_virtualenv": True, "pip_no_cache": True,
        "source_runtime_database_unchanged": True,
        "commands_all_exit_zero": True,
        "browser_visual_verification": "separately recorded, not implied by this script",
    }, indent=2), encoding="utf-8")
    print("CLEAN REPRODUCTION PASSED; workspace location retained in ignored instance file", flush=True)


if __name__ == "__main__":
    main()
