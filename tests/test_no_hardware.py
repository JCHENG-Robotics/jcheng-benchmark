"""Static boundary check: the harness must not reach hardware, DDS or devices.

Only executable and declarative sources are scanned; documentation may name the
robot and its topics.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = (ROOT / "src", ROOT / "scripts", ROOT / "benchmarks")
SUFFIXES = {".py", ".yaml", ".yml", ".sh", ".toml"}

FORBIDDEN = (
    "rclpy",
    "rospy",
    "ros2",
    "/dev/",
    "pyserial",
    "serial.serial",
    "socketcan",
    "can0",
    "pigpio",
    "rpi.gpio",
    "cv2.videocapture",
    "subprocess",
    "os.system",
    "popen",
)


def _source_files():
    for directory in SCAN_DIRS:
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix in SUFFIXES:
                yield path


def test_no_hardware_or_dds_tokens_in_sources() -> None:
    problems = []
    for path in _source_files():
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        # /dev/null is a stream redirect, not a device access.
        text = text.replace("/dev/null", "")
        for token in FORBIDDEN:
            if token in text:
                problems.append(f"{path.relative_to(ROOT)}: {token}")
    assert not problems, "hardware/DDS tokens found:\n" + "\n".join(problems)


def test_manifest_has_no_topics_or_devices() -> None:
    manifest = yaml.safe_load(
        (ROOT / "capability.yaml").read_text(encoding="utf-8")
    )
    assert manifest["topics"] == {"subscribes": [], "publishes": []}
    assert manifest["hardware_access"]["kind"] == "none"
    assert manifest["motion_authority"] == "none"
