"""Prepare a source/document candidate, never a completed course submission.

Requires Git for its tracked/non-ignored inventory. Does not include raw dialogue,
video or runtime storage and never sends or publishes anything.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("docs/DELIVERY_MANIFEST.txt")
ROOT_FILES = {"README.md", "DESIGN.md", "AGENTS.md", "PLANS.md", "run.py",
              "requirements.txt", "requirements-dev.txt", ".gitignore", ".env.example"}
ALLOWED_DIRS = {"app", "tests", "scripts", "docs", "ai_evidence"}
FORBIDDEN_PARTS = {".git", ".venv", "instance", "__pycache__", ".pytest_cache", "conversation_export", "AI对话", "演示视频"}


def candidate_files():
    result = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"],
                            cwd=ROOT, capture_output=True, check=True)
    candidates = set(result.stdout.decode("utf-8").split("\0")) - {""}
    files = []
    for name in sorted(candidates):
        relative = Path(name)
        if name not in ROOT_FILES and relative.parts[0] not in ALLOWED_DIRS:
            continue
        if FORBIDDEN_PARTS.intersection(relative.parts):
            continue
        if relative.suffix.lower() in {".sqlite3", ".sqlite", ".db", ".pyc", ".key", ".pem", ".zip"}:
            continue
        if relative == MANIFEST:
            continue
        target = ROOT / relative
        if target.is_file():
            if target.is_symlink() or not target.resolve().is_relative_to(ROOT):
                raise RuntimeError("Unsafe file in delivery inventory")
            files.append(relative)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="instance/delivery/source-docs-candidate.zip")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to((ROOT / "instance").resolve()):
        parser.error("Output must stay inside ignored instance/ storage")
    files = candidate_files()
    header = ["Source/document candidate manifest — 2026-10-26",
              "NOT a completed submission: raw AI dialogue and real video are missing.",
              "Working-copy SHA256; Git newline conversion may change text hashes.",
              "Manifest excludes itself to avoid circular hashing.", "SHA256  relative_path"]
    hashes = {p.as_posix(): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files}
    (ROOT / MANIFEST).write_text("\n".join(header + [f"{hashes[p.as_posix()]}  {p.as_posix()}" for p in files]) + "\n", encoding="utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for p in files + [MANIFEST]:
            archive.write(ROOT / p, "project/" + p.as_posix())
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(files) + 1
        for name, digest in hashes.items():
            assert hashlib.sha256(archive.read("project/" + name)).hexdigest() == digest
    print(f"Candidate archive verified: {len(files)+1} files; every manifest hash matches.")
    print(f"Output: {output.relative_to(ROOT).as_posix()}")
    print("Raw dialogue/video NOT included; this is not the final five-part submission.")


if __name__ == "__main__":
    main()
