"""Integration test for the live benchmark collector."""

import json
import os
import platform
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
RUNNER = REPO / 'tools' / 'live' / 'run_benchmark.sh'

pytestmark = pytest.mark.skipif(
    platform.system() != 'Linux',
    reason='the host probe reads Linux /proc and /sys',
)


def test_runner_syntax():
    """The collector script parses as bash."""
    result = subprocess.run(
        ['bash', '-n', str(RUNNER)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_runner_laptop_only(tmp_path):
    """A laptop-only run writes a host report without the robot."""
    env = dict(os.environ)
    env['SKIP_ROBOT'] = '1'
    env['SKIP_LAPTOP_ROS'] = '1'
    result = subprocess.run(
        [str(RUNNER), str(tmp_path)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    output = tmp_path / 'laptop_host.json'
    assert output.exists()
    payload = json.loads(output.read_text(encoding='utf-8'))
    assert payload['mode'] == 'host'
    assert payload['cpu']['logical_cores'] >= 1
    # SKIP_ROBOT=1 must also skip ping: the offline test makes no network call.
    assert not (tmp_path / 'ping_robot.txt').exists()


def test_runner_refuses_to_overwrite_evidence(tmp_path):
    """A second run into the same directory is refused, not overwritten."""
    env = dict(os.environ)
    env['SKIP_ROBOT'] = '1'
    env['SKIP_LAPTOP_ROS'] = '1'
    first = subprocess.run(
        [str(RUNNER), str(tmp_path)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )
    assert first.returncode == 0, first.stderr
    second = subprocess.run(
        [str(RUNNER), str(tmp_path)],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )
    assert second.returncode == 4
    assert 'refusing to overwrite' in second.stderr
