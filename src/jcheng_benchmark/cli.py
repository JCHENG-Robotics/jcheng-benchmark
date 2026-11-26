"""Command line entry point for the offline benchmark harness."""

from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path

from .model import BenchmarkError, load_suite
from .report import write_json, write_markdown
from .runner import run_suite

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_INCONCLUSIVE = 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jcheng-benchmark",
        description=(
            "Offline, read-only benchmark harness. It reads a suite and a "
            "recorded JSONL dataset; it never joins DDS, opens a device or "
            "commands motion."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list", help="list suite declarations in a directory"
    )
    list_parser.add_argument("--dir", default="benchmarks/suites")

    validate_parser = subparsers.add_parser(
        "validate", help="validate one or more suite declarations"
    )
    validate_parser.add_argument(
        "--spec", action="append", required=True, help="suite YAML path"
    )

    run_parser = subparsers.add_parser(
        "run", help="run a suite against a JSONL dataset"
    )
    run_parser.add_argument("--spec", required=True, help="suite YAML path")
    run_parser.add_argument("--data", required=True, help="JSONL dataset path")
    run_parser.add_argument("--json", help="write the JSON report here")
    run_parser.add_argument(
        "--markdown", help="write the Markdown report here"
    )
    run_parser.add_argument(
        "--operator", default="unknown", help="operator name for the report"
    )
    run_parser.add_argument(
        "--host", default=socket.gethostname(), help="host name for the report"
    )
    run_parser.add_argument(
        "--note", action="append", default=[], help="repeatable report note"
    )
    return parser


def _list_suites(directory: str) -> int:
    paths = sorted(
        path
        for path in Path(directory).glob("*")
        if path.suffix in (".yaml", ".yml") and path.is_file()
    )
    if not paths:
        print(f"no suite declarations in {directory}")
        return EXIT_INCONCLUSIVE
    failures = 0
    for path in paths:
        try:
            spec = load_suite(path)
        except BenchmarkError as exc:
            print(f"INVALID {path}: {exc}", file=sys.stderr)
            failures += 1
            continue
        print(
            f"{spec.suite}\t{spec.level}\t{spec.data_source}\t"
            f"{len(spec.thresholds)} threshold(s)\t{spec.title}"
        )
    return EXIT_INCONCLUSIVE if failures else EXIT_PASS


def _validate(specs: list[str]) -> int:
    failures = 0
    for spec_path in specs:
        try:
            spec = load_suite(spec_path)
        except BenchmarkError as exc:
            print(f"INVALID {spec_path}: {exc}", file=sys.stderr)
            failures += 1
            continue
        print(
            f"OK {spec_path}: {spec.suite} at {spec.level} "
            f"({spec.data_source})"
        )
    return EXIT_INCONCLUSIVE if failures else EXIT_PASS


def _run(args: argparse.Namespace) -> int:
    spec = load_suite(args.spec)
    report = run_suite(
        spec,
        args.data,
        operator_name=args.operator,
        host=args.host,
        notes=tuple(args.note),
    )
    if args.json:
        write_json(args.json, report)
    if args.markdown:
        write_markdown(args.markdown, report)

    print(
        f"suite: {spec.suite} ({spec.level}, {spec.data_source})"
    )
    print(
        f"dataset: {args.data} "
        f"({report['dataset']['samples']} samples)"
    )
    print(f"result: {report['result']} — {report['result_reason']}")
    for metric_id, metric in report["metrics"].items():
        if metric["kind"] == "success_rate":
            print(f"{metric_id}: rate={metric['rate']:.6g} (count={metric['count']})")
        else:
            print(
                f"{metric_id}: mean={metric['mean']:.6g} "
                f"p95={metric['p95']:.6g} max={metric['max']:.6g} "
                f"{metric['unit']}"
            )
    if args.json:
        print(f"json: {args.json}")
    if args.markdown:
        print(f"markdown: {args.markdown}")

    return {
        "pass": EXIT_PASS,
        "fail": EXIT_FAIL,
        "inconclusive": EXIT_INCONCLUSIVE,
    }[report["result"]]


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "list":
            return _list_suites(args.dir)
        if args.command == "validate":
            return _validate(args.spec)
        if args.command == "run":
            return _run(args)
    except BenchmarkError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_INCONCLUSIVE
    except OSError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_INCONCLUSIVE
    raise AssertionError(f"unhandled command {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
