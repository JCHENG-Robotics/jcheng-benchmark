#!/usr/bin/env bash
# Repository gate for jcheng-benchmark. Run locally or from CI; it touches no
# robot, no device and no network.
#
#   bash scripts/check_repo_gate.sh
#
# It checks: required files, no LICENSE, shell/Python syntax, the no-hardware
# boundary, secret/weight scans, every shipped suite, the test suite, the
# synthetic self-test and relative documentation links.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail() { printf 'GATE FAIL: %s\n' "$*" >&2; exit 1; }
step() { printf '== %s\n' "$*"; }

step "required files"
while IFS= read -r path; do
    [[ -e "$path" ]] || fail "missing $path"
done <<'EOF'
README.md
README.zh-CN.md
ROADMAP.md
CHANGELOG.md
ACCEPTANCE.md
VERSION
LICENSE-REVIEW.md
capability.yaml
pyproject.toml
docs/ARCHITECTURE.md
docs/BENCHMARK_PROTOCOL.md
docs/EVIDENCE.md
benchmarks/README.md
evidence/README.md
scripts/check_repo_gate.sh
.github/CODEOWNERS
.github/workflows/ci.yml
src/jcheng_benchmark/__init__.py
src/jcheng_benchmark/__main__.py
src/jcheng_benchmark/cli.py
src/jcheng_benchmark/model.py
src/jcheng_benchmark/report.py
src/jcheng_benchmark/runner.py
src/jcheng_benchmark/stats.py
tests/fixtures/synthetic/suite.yaml
tests/fixtures/synthetic/samples.jsonl
tools/live/README.md
tools/live/host_benchmark.py
tools/live/run_benchmark.sh
tools/live/tests/test_host_benchmark.py
tools/live/tests/test_run_benchmark.py
evidence/host_benchmark_20261117_session4/README.md
EOF

step "no LICENSE before the review closes"
[[ ! -e LICENSE ]] || fail "LICENSE must not exist before the license review closes"

step "shell syntax"
while IFS= read -r script; do
    bash -n "$script" || fail "bash -n $script"
done < <(find scripts tools -name '*.sh' -type f | sort)

step "python syntax"
python3 -m compileall -q src tests tools/live

step "no hardware or DDS access"
python3 -m pytest -q tests/test_no_hardware.py

step "live probe confinement"
python3 -m pytest -q tests/test_live_probe_boundary.py

step "secret scan"
if grep -rInE \
        'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----' \
        --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ \
        --exclude='check_repo_gate.sh' . >/dev/null 2>&1; then
    fail "possible secret material found"
fi
if find . -path ./.git -prune -o -path ./.venv -prune -o \
        -name '*.env' -print | grep -q .; then
    fail "*.env files must stay outside the repository"
fi
if find . -path ./.git -prune -o -path ./.venv -prune -o \
        \( -name '*.pt' -o -name '*.onnx' -o -name '*.engine' \
        -o -name '*.bag' -o -name '*.db3' -o -name '*.mcap' \) \
        -print | grep -q .; then
    fail "model weights and recorded bags must stay outside the repository"
fi

step "suite declarations"
for spec in benchmarks/suites/*.yaml; do
    [[ -e "$spec" ]] || fail "no suite declarations found"
    PYTHONPATH=src python3 -m jcheng_benchmark validate --spec "$spec"
done

step "tests"
python3 -m pytest -q

step "synthetic self-test"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
PYTHONPATH=src python3 -m jcheng_benchmark run \
    --spec tests/fixtures/synthetic/suite.yaml \
    --data tests/fixtures/synthetic/samples.jsonl \
    --operator gate --host local \
    --json "$tmpdir/report.json" --markdown "$tmpdir/report.md" >/dev/null
python3 - "$tmpdir/report.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    report = json.load(handle)
assert report["result"] == "pass", report["result"]
assert report["suite"]["data_source"] == "synthetic"
assert any("not a hardware" in item for item in report["limitations"])
print("synthetic self-test report is labelled synthetic")
PY

step "docs links"
python3 - <<'PY'
import re
import sys
from pathlib import Path

documents = [
    Path("README.md"),
    Path("README.zh-CN.md"),
    Path("ROADMAP.md"),
    Path("ACCEPTANCE.md"),
    Path("CHANGELOG.md"),
    Path("LICENSE-REVIEW.md"),
    *sorted(Path("docs").glob("*.md")),
    Path("benchmarks/README.md"),
    Path("evidence/README.md"),
    Path("tools/live/README.md"),
    Path("evidence/host_benchmark_20261117_session4/README.md"),
]

problems = []
for document in documents:
    text = document.read_text(encoding="utf-8")
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        path = target.split("#", 1)[0].split("?", 1)[0]
        if not path:
            continue
        if not (document.parent / path).resolve().exists():
            problems.append(f"{document}: {target}")
if problems:
    print("broken relative links:", *problems, sep="\n  ")
    sys.exit(1)
print("all relative links resolve")
PY

step "gate OK"
