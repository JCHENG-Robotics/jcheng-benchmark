from __future__ import annotations

from pathlib import Path

import yaml

from jcheng_benchmark import __version__
from jcheng_benchmark.model import load_suite

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = (
    "README.md",
    "README.zh-CN.md",
    "ROADMAP.md",
    "CHANGELOG.md",
    "ACCEPTANCE.md",
    "VERSION",
    "LICENSE-REVIEW.md",
    "capability.yaml",
    "pyproject.toml",
    "docs/ARCHITECTURE.md",
    "docs/BENCHMARK_PROTOCOL.md",
    "docs/EVIDENCE.md",
    "benchmarks/README.md",
    "evidence/README.md",
    "scripts/check_repo_gate.sh",
    ".github/CODEOWNERS",
    ".github/workflows/ci.yml",
)


def test_required_files_exist() -> None:
    missing = [path for path in REQUIRED if not (ROOT / path).is_file()]
    assert not missing, f"missing: {missing}"


def test_version_matches_package_and_manifest() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    manifest = yaml.safe_load(
        (ROOT / "capability.yaml").read_text(encoding="utf-8")
    )
    assert version == __version__ == manifest["version"] == "0.1.0"


def test_capability_manifest_is_offline_and_read_only() -> None:
    manifest = yaml.safe_load(
        (ROOT / "capability.yaml").read_text(encoding="utf-8")
    )
    assert manifest["name"] == "jcheng-benchmark"
    assert manifest["layer"] == "bench"
    assert manifest["status"] == "experimental"
    assert manifest["hardware_access"]["kind"] == "none"
    assert manifest["motion_authority"] == "none"
    assert manifest["control_path"] == "none"
    assert manifest["fail_closed"] is True
    assert manifest["topics"] == {"subscribes": [], "publishes": []}
    assert manifest["runtime_roles"]


def test_no_license_before_review() -> None:
    assert not (ROOT / "LICENSE").exists()
    text = (ROOT / "LICENSE-REVIEW.md").read_text(encoding="utf-8")
    assert "does **not** ship a `LICENSE`" in text


def test_no_model_weights_or_recorded_bags() -> None:
    suffixes = {".pt", ".onnx", ".engine", ".bag", ".db3", ".mcap"}
    found = [
        path.relative_to(ROOT)
        for path in ROOT.rglob("*")
        if path.is_file() and path.suffix in suffixes
    ]
    assert not found, f"model weights or bags must stay out of the tree: {found}"


def test_readme_has_status_block_and_boundary() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert text.startswith("# jcheng-benchmark")
    assert "> Status: **Experimental**" in text
    assert "| Hardware access |" in text


def test_chinese_readme_is_a_translation_pointer() -> None:
    text = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    assert "本文为英文主文档的中文对照" in text
    assert "README.md" in text


def test_changelog_starts_with_the_release() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert text.startswith("# Changelog")
    assert "## [Unreleased]" in text
    assert "## [0.1.0] — 2026-11-26" in text


def test_ci_runs_the_repository_gate() -> None:
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    assert "benchmark-gate" in text
    assert "bash scripts/check_repo_gate.sh" in text


def test_every_shipped_suite_validates() -> None:
    paths = sorted((ROOT / "benchmarks" / "suites").glob("*.yaml"))
    assert paths, "at least one suite declaration must ship"
    for path in paths:
        spec = load_suite(path)
        assert spec.metrics
