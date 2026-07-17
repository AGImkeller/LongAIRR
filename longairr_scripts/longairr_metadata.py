#!/usr/bin/env python3

import argparse
import fcntl
import json
import os
import re
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

#================================================================#
#
#        Script:  longairr_metadata.py
#         Usage:  Internal script used in all longairr modules to write run and 
#                 module specific metadata later used to write a run report.
#
#   DESCRIPTION:  Script provides a metadata scheme used within each longairr
#                 module to write run and module specific parameters, file-paths
#                 and read-counts into a metadata file, which is later further
#                 further processed by 'longairr report'.
#
#        AUTHOR:  Jonas Schuck, jschuckdev@gmail.com
#    BUG-REPORT:  https://github.com/AGImkeller/LongAIRR/issues
#
#================================================================#

SCHEMA_VERSION = 1
RECORD_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")


def now_local_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def atomic_write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_path = Path(handle.name)
            json.dump(data, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(tmp_path, path)
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink()


def find_existing_run_root(start_path):
    for candidate in (start_path, *start_path.parents):
        if (candidate / ".longairr" / "run.json").is_file():
            return candidate
    return None


def resolve_run_root(output_path, requested_run_root=None):
    output = Path(output_path).expanduser().resolve()
    if not output.is_dir():
        raise ValueError(f"Output directory does not exist: {output}")

    if requested_run_root:
        run_root = Path(requested_run_root).expanduser().resolve()
        if not run_root.is_dir():
            raise ValueError(f"Specified run root does not exist: {run_root}")
        return run_root

    existing_root = find_existing_run_root(output)
    return existing_root if existing_root is not None else output


def load_json(path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {path}") from exc


def initialize_run(run_root, longairr_version):
    state_dir = run_root / ".longairr"
    state_dir.mkdir(parents=True, exist_ok=True)

    run_file = state_dir / "run.json"
    lock_file = state_dir / "run.lock"

    with lock_file.open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)

        if run_file.exists():
            run_data = load_json(run_file)
            if not run_data.get("run_id"):
                raise ValueError(f"Run marker is missing 'run_id': {run_file}")
            return run_data

        run_data = {
            "schema_version": SCHEMA_VERSION,
            "run_id": str(uuid.uuid4()),
            "longairr_version": longairr_version,
            "run_root": str(run_root),
            "created_at": now_local_iso(),
        }
        atomic_write_json(run_file, run_data)
        return run_data


def parse_scalar(value):
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def parse_key_value(items, value_parser, argument_name):
    parsed = {}

    for item in items or []:
        if "=" not in item:
            raise ValueError(f"{argument_name} must use KEY=VALUE format: {item}")

        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"{argument_name} contains an empty key: {item}")

        parsed[key] = value_parser(value)

    return parsed


def parse_count(value):
    try:
        count = int(value)
    except ValueError as exc:
        raise ValueError(f"Count must be an integer: {value}") from exc

    if count < 0:
        raise ValueError(f"Count must be >= 0: {value}")
    return count


def parse_file_path(value):
    return str(Path(value).expanduser().resolve())


def sanitize_record_id(record_id):
    cleaned = RECORD_ID_RE.sub("_", record_id.strip()).strip("._")
    if not cleaned:
        raise ValueError("Record ID must contain at least one letter or number")
    return cleaned


def build_scope(scope_type, sample=None, locus=None):
    scope = {"type": scope_type}

    if scope_type in {"sample", "sample_locus"}:
        if not sample:
            raise ValueError(f"--sample is required for scope type '{scope_type}'")
        scope["sample"] = sample

    if scope_type in {"locus", "sample_locus"}:
        if not locus:
            raise ValueError(f"--locus is required for scope type '{scope_type}'")
        scope["locus"] = locus.lower()

    return scope


def calculate_duration_seconds(started_at, finished_at):
    try:
        started = datetime.fromisoformat(started_at)
        finished = datetime.fromisoformat(finished_at)
    except ValueError:
        return None

    return max(0.0, round((finished - started).total_seconds(), 3))


def command_init_run(args):
    run_root = resolve_run_root(args.output, args.run_root)
    initialize_run(run_root, args.longairr_version)
    print(run_root)


def command_write_module(args):
    run_root = Path(args.run_root).expanduser().resolve()
    run_file = run_root / ".longairr" / "run.json"
    if not run_file.is_file():
        raise ValueError(
            f"LongAIRR run marker not found: {run_file}. "
            "Initialize the run before writing module metadata."
        )

    run_data = load_json(run_file)
    record_id = sanitize_record_id(args.record_id)
    scope = build_scope(args.scope_type, sample=args.sample, locus=args.locus)

    parameters = parse_key_value(args.parameter, parse_scalar, "--parameter")
    counts = parse_key_value(args.count, parse_count, "--count")
    files = parse_key_value(args.file, parse_file_path, "--file")

    module_data = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_data["run_id"],
        "longairr_version": args.longairr_version,
        "module": args.module,
        "record_id": record_id,
        "scope": scope,
        "status": args.status,
        "started_at": args.started_at,
        "finished_at": args.finished_at,
        "parameters": parameters,
        "counts": counts,
        "files": files,
    }

    duration = calculate_duration_seconds(args.started_at, args.finished_at)
    if duration is not None:
        module_data["duration_seconds"] = duration

    metadata_file = (
        run_root
        / ".longairr"
        / "metadata"
        / args.module
        / f"{record_id}.json"
    )
    atomic_write_json(metadata_file, module_data)
    print(metadata_file)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Initialize LongAIRR runs and write structured module metadata."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init-run",
        help="Resolve and initialize a LongAIRR run root.",
    )
    init_parser.add_argument("--output", required=True, help="Module output directory")
    init_parser.add_argument(
        "--run-root",
        help="Explicit LongAIRR run root. Otherwise an existing marker is searched for above --output.",
    )
    init_parser.add_argument(
        "--longairr-version",
        required=True,
        help="LongAIRR version stored in the run marker",
    )
    init_parser.set_defaults(func=command_init_run)

    module_parser = subparsers.add_parser(
        "write-module",
        help="Write one module metadata record.",
    )
    module_parser.add_argument("--run-root", required=True)
    module_parser.add_argument("--module", required=True)
    module_parser.add_argument("--longairr-version", required=True)
    module_parser.add_argument("--record-id", required=True)
    module_parser.add_argument(
        "--scope-type",
        required=True,
        choices=("run", "sample", "locus", "sample_locus"),
    )
    module_parser.add_argument("--sample")
    module_parser.add_argument("--locus")
    module_parser.add_argument(
        "--status",
        default="success",
        choices=("success", "failed", "skipped"),
    )
    module_parser.add_argument("--started-at", required=True)
    module_parser.add_argument("--finished-at", required=True)
    module_parser.add_argument("--parameter", action="append", default=[])
    module_parser.add_argument("--count", action="append", default=[])
    module_parser.add_argument("--file", action="append", default=[])
    module_parser.set_defaults(func=command_write_module)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        args.func(args)
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
