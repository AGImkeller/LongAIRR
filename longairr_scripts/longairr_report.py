#!/usr/bin/env python3

from __future__ import annotations

import argparse
import base64
import csv
import html as html_lib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

#================================================================#
#
#        Script:  longairr_report.py
#         Usage:  Internal script used in 'longairr.sh/longairr report'
#
#   DESCRIPTION:  Combines metadata and logging information across longairr
#                 modules into a count-overview 'summary.tsv' and 
#                 HTML-report with deterministic structure, independent of
#                 completion when running parallel processes. 
#                 This module can be used seperately at any stage of a full longairr run,
#                 e.g., after running 'longairr filter' and 'longairr collapse', or
#                 will be automatically executed at the end of 'longairr airr'
#
#        AUTHOR:  Jonas Schuck, jschuckdev@gmail.com
#    BUG-REPORT:  https://github.com/AGImkeller/LongAIRR/issues
#
#================================================================#

SCHEMA_VERSION = 1
SUPPORTED_SCOPE_TYPES = {"run", "sample", "locus", "sample_locus"}
SUPPORTED_STATUSES = {"success", "failed", "skipped"}
MODULE_ORDER = {
    "basecall": 0,
    "filter": 10,
    "demux": 20,
    "collapse": 30,
    "seqtag": 40,
    "airr": 50,
}
LOCUS_ORDER = {
    "ig": 0,
    "tr": 1,
}
SPLIT_COUNT_RE = re.compile(r"^split_(.+)_sequences$")

# Raised when report metadata is invalid (e.g., different runID)
class ReportError(Exception):
    pass

# Class for one module metadata record
@dataclass(frozen=True)
class ModuleRecord:

    source_path: Path
    schema_version: int
    run_id: str
    longairr_version: str
    module: str
    record_id: str
    scope: Mapping[str, str]
    status: str
    started_at: str
    finished_at: str
    parameters: Mapping[str, Any]
    counts: Mapping[str, int]
    files: Mapping[str, str]
    duration_seconds: float | None
    raw: Mapping[str, Any] = field(repr=False)

    @property
    def scope_type(self) -> str:
        return self.scope["type"]

    @property
    def sample(self) -> str | None:
        return self.scope.get("sample")

    @property
    def locus(self) -> str | None:
        locus = self.scope.get("locus")
        return locus.lower() if locus else None



# Longairr 'run' metadata class
@dataclass
class ReportModel:

    run_root: Path
    run_data: Mapping[str, Any]
    records: list[ModuleRecord]
    warnings: list[str] = field(default_factory=list)

    @property
    def run_id(self) -> str:
        return str(self.run_data["run_id"])

    @property
    def longairr_version(self) -> str:
        return str(self.run_data["longairr_version"])

    def records_for(self, module: str) -> list[ModuleRecord]:
        return [record for record in self.records if record.module == module]


# definition for one row in the summary.tsv overview table
@dataclass(frozen=True)
class SummaryRow:

    step: str
    path_info: str
    date: str
    input_reads: int
    output_reads: int
    percent_retained: float | None
    input_description: str
    output_description: str

    def as_cells(self) -> list[str]:
        percent = (
            ""
            if self.percent_retained is None
            else f"{self.percent_retained:.1f}%"
        )
        return [
            _clean_cell(self.step),
            _clean_cell(self.path_info),
            _clean_cell(self.date),
            str(self.input_reads),
            str(self.output_reads),
            percent,
            _clean_cell(self.input_description),
            _clean_cell(self.output_description),
        ]



# generate one line per summary entry
def _clean_cell(value: Any) -> str:

    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ReportError(f"Invalid JSON file: {path}") from exc
    except OSError as exc:
        raise ReportError(f"Could not read JSON file: {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ReportError(f"JSON root must be an object: {path}")
    return data


def _require_string(
    data: Mapping[str, Any],
    key: str,
    path: Path,
    *,
    allow_empty: bool = False,
) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ReportError(f"'{key}' must be a string: {path}")
    if not allow_empty and not value.strip():
        raise ReportError(f"'{key}' must not be empty: {path}")
    return value


def _require_int(data: Mapping[str, Any], key: str, path: Path) -> int:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReportError(f"'{key}' must be an integer: {path}")
    return value


def _require_dict(data: Mapping[str, Any], key: str, path: Path) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ReportError(f"'{key}' must be an object: {path}")
    return value


def _parse_iso_datetime(value: str, key: str, path: Path) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ReportError(
            f"'{key}' must be an ISO-8601 datetime in {path}: {value}"
        ) from exc


def _validate_run_marker(
    run_root: Path,
    run_file: Path,
    data: Mapping[str, Any],
    warnings: list[str],
) -> None:
    schema_version = _require_int(data, "schema_version", run_file)
    if schema_version != SCHEMA_VERSION:
        raise ReportError(
            f"Unsupported run schema_version {schema_version} in {run_file}; "
            f"supported version is {SCHEMA_VERSION}."
        )

    _require_string(data, "run_id", run_file)
    _require_string(data, "longairr_version", run_file)
    _require_string(data, "created_at", run_file)
    _parse_iso_datetime(str(data["created_at"]), "created_at", run_file)

    marker_root = data.get("run_root")
    if isinstance(marker_root, str) and marker_root:
        marker_path = Path(marker_root).expanduser()
        try:
            marker_path = marker_path.resolve()
        except OSError:
            pass
        if marker_path != run_root:
            warnings.append(
                "The run marker's stored run_root differs from the directory "
                f"being reported: marker={marker_path}, requested={run_root}."
            )


def _validate_scope(scope: Mapping[str, Any], path: Path) -> dict[str, str]:
    scope_type = scope.get("type")
    if scope_type not in SUPPORTED_SCOPE_TYPES:
        raise ReportError(
            f"Unsupported scope type in {path}: {scope_type!r}. "
            f"Allowed values: {', '.join(sorted(SUPPORTED_SCOPE_TYPES))}."
        )

    normalized: dict[str, str] = {"type": str(scope_type)}

    if scope_type in {"sample", "sample_locus"}:
        sample = scope.get("sample")
        if not isinstance(sample, str) or not sample.strip():
            raise ReportError(
                f"Scope type '{scope_type}' requires a non-empty sample: {path}"
            )
        normalized["sample"] = sample

    if scope_type in {"locus", "sample_locus"}:
        locus = scope.get("locus")
        if not isinstance(locus, str) or not locus.strip():
            raise ReportError(
                f"Scope type '{scope_type}' requires a non-empty locus: {path}"
            )
        normalized["locus"] = locus.lower()

    return normalized


def _validate_record(
    path: Path,
    data: Mapping[str, Any],
    run_data: Mapping[str, Any],
    expected_module: str,
    warnings: list[str],
) -> ModuleRecord:
    schema_version = _require_int(data, "schema_version", path)
    if schema_version != SCHEMA_VERSION:
        raise ReportError(
            f"Unsupported metadata schema_version {schema_version} in {path}; "
            f"supported version is {SCHEMA_VERSION}."
        )

    run_id = _require_string(data, "run_id", path)
    if run_id != run_data["run_id"]:
        raise ReportError(
            f"Metadata run_id does not match the run marker: {path}"
        )

    longairr_version = _require_string(data, "longairr_version", path)
    if longairr_version != run_data["longairr_version"]:
        warnings.append(
            f"LongAIRR version mismatch in {path}: record={longairr_version}, "
            f"run={run_data['longairr_version']}."
        )

    module = _require_string(data, "module", path)
    if module != expected_module:
        raise ReportError(
            f"Metadata module '{module}' does not match its directory "
            f"'{expected_module}': {path}"
        )

    record_id = _require_string(data, "record_id", path)
    if path.stem != record_id:
        raise ReportError(
            f"Metadata record_id '{record_id}' does not match filename "
            f"'{path.name}'."
        )

    scope = _validate_scope(_require_dict(data, "scope", path), path)

    status = _require_string(data, "status", path)
    if status not in SUPPORTED_STATUSES:
        raise ReportError(
            f"Unsupported metadata status in {path}: {status!r}."
        )

    started_at = _require_string(data, "started_at", path)
    finished_at = _require_string(data, "finished_at", path)
    started = _parse_iso_datetime(started_at, "started_at", path)
    finished = _parse_iso_datetime(finished_at, "finished_at", path)
    if finished < started:
        raise ReportError(
            f"finished_at precedes started_at in metadata record: {path}"
        )

    parameters = _require_dict(data, "parameters", path)
    counts_raw = _require_dict(data, "counts", path)
    files_raw = _require_dict(data, "files", path)

    counts: dict[str, int] = {}
    for key, value in counts_raw.items():
        if not isinstance(key, str) or not key:
            raise ReportError(f"Count keys must be non-empty strings: {path}")
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ReportError(
                f"Count '{key}' must be a non-negative integer: {path}"
            )
        counts[key] = value

    files: dict[str, str] = {}
    for key, value in files_raw.items():
        if not isinstance(key, str) or not key:
            raise ReportError(f"File keys must be non-empty strings: {path}")
        if not isinstance(value, str) or not value:
            raise ReportError(
                f"File '{key}' must be a non-empty path string: {path}"
            )
        files[key] = value

    duration_value = data.get("duration_seconds")
    duration_seconds: float | None
    if duration_value is None:
        duration_seconds = None
    elif (
        isinstance(duration_value, bool)
        or not isinstance(duration_value, (int, float))
        or duration_value < 0
    ):
        raise ReportError(
            f"'duration_seconds' must be a non-negative number: {path}"
        )
    else:
        duration_seconds = float(duration_value)

    return ModuleRecord(
        source_path=path,
        schema_version=schema_version,
        run_id=run_id,
        longairr_version=longairr_version,
        module=module,
        record_id=record_id,
        scope=scope,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        parameters=parameters,
        counts=counts,
        files=files,
        duration_seconds=duration_seconds,
        raw=dict(data),
    )


def _record_sort_key(record: ModuleRecord) -> tuple[Any, ...]:
    sample = record.sample or ""
    locus = record.locus or ""
    return (
        MODULE_ORDER.get(record.module, 1000),
        record.module,
        sample,
        LOCUS_ORDER.get(locus, 100),
        locus,
        record.record_id,
    )


# Load metadata across one LongAIRR run (all modules contained in .longairr)
def load_report_model(run_root: str | Path) -> ReportModel:

    resolved_root = Path(run_root).expanduser().resolve()
    if not resolved_root.is_dir():
        raise ReportError(f"Run root does not exist: {resolved_root}")

    run_file = resolved_root / ".longairr" / "run.json"
    if not run_file.is_file():
        raise ReportError(f"LongAIRR run marker not found: {run_file}")

    warnings: list[str] = []
    run_data = _load_json_object(run_file)
    _validate_run_marker(resolved_root, run_file, run_data, warnings)

    metadata_root = resolved_root / ".longairr" / "metadata"
    records: list[ModuleRecord] = []
    seen: set[tuple[str, str]] = set()

    if metadata_root.is_dir():
        for path in sorted(metadata_root.rglob("*.json")):
            relative = path.relative_to(metadata_root)
            if len(relative.parts) < 2:
                raise ReportError(
                    f"Metadata JSON must be stored below a module directory: {path}"
                )

            expected_module = relative.parts[0]
            data = _load_json_object(path)
            record = _validate_record(
                path,
                data,
                run_data,
                expected_module,
                warnings,
            )

            key = (record.module, record.record_id)
            if key in seen:
                raise ReportError(
                    f"Duplicate module/record combination: "
                    f"{record.module}/{record.record_id}"
                )
            seen.add(key)
            records.append(record)

    records.sort(key=_record_sort_key)

    model = ReportModel(
        run_root=resolved_root,
        run_data=run_data,
        records=records,
        warnings=warnings,
    )

    if not records:
        model.warnings.append(
            f"No module metadata records were found below {metadata_root}."
        )

    validate_count_relationships(model)
    return model


def _count(record: ModuleRecord, key: str) -> int | None:
    value = record.counts.get(key)
    return value if isinstance(value, int) else None


def _percent(output_count: int, input_count: int) -> float | None:
    if input_count <= 0:
        return None
    return output_count * 100.0 / input_count


def _format_date(value: str) -> str:
    return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M:%S")


def _locus_label(value: str) -> str:
    normalized = value.lower()
    if normalized == "ig":
        return "Ig"
    if normalized in {"tr", "tcr"}:
        return "TCR"
    return value.upper()


def _main_path_info(record: ModuleRecord, run_root: Path) -> str:
    if record.scope_type in {"sample", "sample_locus"} and record.sample:
        return record.sample
    if record.scope_type in {"locus", "sample_locus"} and record.locus:
        return _locus_label(record.locus)
    return run_root.name


def _stage_path_info(record: ModuleRecord, stage: str) -> str:
    if record.sample:
        return f"{record.sample} | {stage}"
    return stage


def _add_transition(
    rows: list[SummaryRow],
    *,
    record: ModuleRecord,
    step: str,
    path_info: str,
    input_count: int | None,
    output_count: int | None,
    input_description: str,
    output_description: str,
) -> None:
    if input_count is None or output_count is None:
        return

    rows.append(
        SummaryRow(
            step=step,
            path_info=path_info,
            date=_format_date(record.finished_at),
            input_reads=input_count,
            output_reads=output_count,
            percent_retained=_percent(output_count, input_count),
            input_description=input_description,
            output_description=output_description,
        )
    )


def _filter_rows(record: ModuleRecord, run_root: Path) -> list[SummaryRow]:
    rows: list[SummaryRow] = []
    minimum_quality = record.parameters.get("min_quality")
    output_description = "Filtered reads"
    if minimum_quality is not None:
        output_description += f" (minimum quality: {minimum_quality})"

    _add_transition(
        rows,
        record=record,
        step="Filtering",
        path_info=_main_path_info(record, run_root),
        input_count=_count(record, "input_reads"),
        output_count=_count(record, "filtered_reads"),
        input_description="Unfiltered reads",
        output_description=output_description,
    )
    return rows


def _collapse_rows(record: ModuleRecord) -> list[SummaryRow]:
    rows: list[SummaryRow] = []
    library = str(record.parameters.get("library", "")).lower()

    if library == "visiumhd":
        annotated_description = (
            "Reads with valid Visium HD spatial barcode/UMI annotation"
        )
    elif library == "visium":
        annotated_description = (
            "Reads with valid spatial barcode/UMI annotation"
        )
    elif library == "bulk":
        annotated_description = "Reads with valid UMI annotation"
    else:
        annotated_description = "Reads with valid barcode/UMI annotation"

    input_reads = _count(record, "input_reads")
    annotated_reads = _count(record, "annotated_reads")
    length_filtered_reads = _count(record, "length_filtered_reads")
    retained_reads = _count(record, "retained_group_reads")
    consensus_sequences = _count(record, "consensus_sequences")

    _add_transition(
        rows,
        record=record,
        step="Collapse",
        path_info=_stage_path_info(record, "Annotation"),
        input_count=input_reads,
        output_count=annotated_reads,
        input_description="Reads entering collapse",
        output_description=annotated_description,
    )
    _add_transition(
        rows,
        record=record,
        step="Collapse",
        path_info=_stage_path_info(record, "Length filtering"),
        input_count=annotated_reads,
        output_count=length_filtered_reads,
        input_description="Annotated reads",
        output_description="Annotated reads passing length filters",
    )
    _add_transition(
        rows,
        record=record,
        step="Collapse",
        path_info=_stage_path_info(record, "Group retention"),
        input_count=length_filtered_reads,
        output_count=retained_reads,
        input_description="Length-filtered reads",
        output_description="Reads retained for consensus generation",
    )
    _add_transition(
        rows,
        record=record,
        step="Collapse",
        path_info=_stage_path_info(record, "Consensus"),
        input_count=retained_reads,
        output_count=consensus_sequences,
        input_description="Reads retained in receptor groups",
        output_description="Consensus sequences generated",
    )
    return rows


def _split_key_sort_key(key: str) -> tuple[int, str]:
    normalized = key.lower()
    return (LOCUS_ORDER.get(normalized, 100), normalized)


def _seqtag_rows(record: ModuleRecord, run_root: Path) -> list[SummaryRow]:
    rows: list[SummaryRow] = []
    input_sequences = _count(record, "input_sequences")
    matched_sequences = _count(record, "matched_sequences")

    _add_transition(
        rows,
        record=record,
        step="Seqtag",
        path_info=_main_path_info(record, run_root),
        input_count=input_sequences,
        output_count=matched_sequences,
        input_description="Consensus sequences",
        output_description="Sequences matching provided seqtag anchors",
    )

    split_keys: list[tuple[str, str]] = []
    for count_key in record.counts:
        match = SPLIT_COUNT_RE.match(count_key)
        if match:
            split_keys.append((match.group(1), count_key))

    for split_key, count_key in sorted(
        split_keys,
        key=lambda item: _split_key_sort_key(item[0]),
    ):
        label = _locus_label(split_key)
        path_info = label if not record.sample else f"{record.sample} | {label}"
        _add_transition(
            rows,
            record=record,
            step="Seqtag",
            path_info=path_info,
            input_count=matched_sequences,
            output_count=_count(record, count_key),
            input_description="Sequences matching provided seqtag anchors",
            output_description=f"Sequences assigned to {label}",
        )

    return rows


def _airr_rows(record: ModuleRecord) -> list[SummaryRow]:
    rows: list[SummaryRow] = []
    locus = record.locus or str(record.parameters.get("locus", record.record_id))
    locus_label = _locus_label(locus)
    path_info = (
        locus_label
        if not record.sample
        else f"{record.sample} | {locus_label}"
    )

    input_sequences = _count(record, "input_sequences")
    airr_sequences = _count(record, "airr_sequences")
    productive_sequences = _count(record, "productive_sequences")
    productive_heavy_sequences = _count(
        record,
        "productive_heavy_sequences",
    )

    _add_transition(
        rows,
        record=record,
        step="AIRR",
        path_info=path_info,
        input_count=input_sequences,
        output_count=airr_sequences,
        input_description="Sequences provided to AIRR annotation",
        output_description="Sequences with valid V(D)J annotation",
    )

    _add_transition(
        rows,
        record=record,
        step="AIRR",
        path_info=path_info,
        input_count=airr_sequences,
        output_count=productive_sequences,
        input_description="Sequences with valid V(D)J annotation",
        output_description="Productive receptor sequences",
    )

    _add_transition(
        rows,
        record=record,
        step="AIRR",
        path_info=path_info,
        input_count=productive_sequences,
        output_count=productive_heavy_sequences,
        input_description="Productive immunoglobulin receptor sequences",
        output_description="Productive heavy-chain receptor sequences",
    )

    final_output = (
        productive_sequences
        if productive_sequences is not None
        else airr_sequences
    )
    final_description = (
        "Productive receptor sequences"
        if productive_sequences is not None
        else "Sequences with valid V(D)J annotation"
    )
    _add_transition(
        rows,
        record=record,
        step=">AIRRRate",
        path_info=path_info,
        input_count=input_sequences,
        output_count=final_output,
        input_description="Sequences provided to AIRR annotation",
        output_description=final_description,
    )

    return rows


# Define order of rows presented in summary.tsv
def build_summary_rows(model: ReportModel) -> list[SummaryRow]:

    rows: list[SummaryRow] = []

    for record in model.records:
        if record.module == "filter":
            rows.extend(_filter_rows(record, model.run_root))
        elif record.module == "collapse":
            rows.extend(_collapse_rows(record))
        elif record.module == "seqtag":
            rows.extend(_seqtag_rows(record, model.run_root))
        elif record.module == "airr":
            rows.extend(_airr_rows(record))

    return rows


def _warn_if_not_nonincreasing(
    model: ReportModel,
    record: ModuleRecord,
    keys: Sequence[str],
) -> None:
    previous_key: str | None = None
    previous_value: int | None = None

    for key in keys:
        value = _count(record, key)
        if value is None:
            continue
        if previous_value is not None and value > previous_value:
            model.warnings.append(
                f"{record.module}/{record.record_id}: '{key}' ({value}) "
                f"exceeds '{previous_key}' ({previous_value})."
            )
        previous_key = key
        previous_value = value


def _warn_mismatch(
    model: ReportModel,
    left_label: str,
    left_value: int | None,
    right_label: str,
    right_value: int | None,
) -> None:
    if (
        left_value is not None
        and right_value is not None
        and left_value != right_value
    ):
        model.warnings.append(
            f"Count mismatch: {left_label}={left_value}, "
            f"{right_label}={right_value}."
        )


def _find_record(
    model: ReportModel,
    module: str,
    *,
    scope_type: str | None = None,
    sample: str | None = None,
    locus: str | None = None,
) -> ModuleRecord | None:
    for record in model.records_for(module):
        if scope_type is not None and record.scope_type != scope_type:
            continue
        if sample is not None and record.sample != sample:
            continue
        if locus is not None and record.locus != locus.lower():
            continue
        return record
    return None


def _seqtag_split_count(record: ModuleRecord, locus: str) -> int | None:
    candidates = (
        ("split_ig_sequences",)
        if locus == "ig"
        else ("split_tr_sequences", "split_tcr_sequences")
    )
    for key in candidates:
        value = _count(record, key)
        if value is not None:
            return value
    return None


# Validity check
# Warnings if counts passing from one module to another are inconsistent
def validate_count_relationships(model: ReportModel) -> None:
    """Add non-fatal warnings for logically inconsistent count chains."""

    for record in model.records:
        if record.module == "filter":
            _warn_if_not_nonincreasing(
                model,
                record,
                ("input_reads", "filtered_reads"),
            )
        elif record.module == "collapse":
            _warn_if_not_nonincreasing(
                model,
                record,
                (
                    "input_reads",
                    "annotated_reads",
                    "length_filtered_reads",
                    "retained_group_reads",
                    "consensus_sequences",
                ),
            )
        elif record.module == "seqtag":
            _warn_if_not_nonincreasing(
                model,
                record,
                ("input_sequences", "matched_sequences"),
            )
            input_sequences = _count(record, "input_sequences")
            matched = _count(record, "matched_sequences")
            failed = _count(record, "failed_sequences")
            if (
                input_sequences is not None
                and matched is not None
                and failed is not None
                and matched + failed != input_sequences
            ):
                model.warnings.append(
                    f"seqtag/{record.record_id}: matched_sequences + "
                    f"failed_sequences ({matched + failed}) does not equal "
                    f"input_sequences ({input_sequences})."
                )

            split_counts = [
                value
                for key, value in record.counts.items()
                if SPLIT_COUNT_RE.match(key)
            ]
            if (
                split_counts
                and matched is not None
                and sum(split_counts) != matched
            ):
                model.warnings.append(
                    f"seqtag/{record.record_id}: split sequence counts "
                    f"sum to {sum(split_counts)}, but matched_sequences is "
                    f"{matched}."
                )
        elif record.module == "airr":
            _warn_if_not_nonincreasing(
                model,
                record,
                (
                    "input_sequences",
                    "airr_sequences",
                    "productive_sequences",
                    "productive_heavy_sequences",
                ),
            )

    filter_run = _find_record(model, "filter", scope_type="run")
    collapse_run = _find_record(model, "collapse", scope_type="run")
    seqtag_run = _find_record(model, "seqtag", scope_type="run")

    if filter_run and collapse_run:
        _warn_mismatch(
            model,
            "filter/run filtered_reads",
            _count(filter_run, "filtered_reads"),
            "collapse/run input_reads",
            _count(collapse_run, "input_reads"),
        )

    if collapse_run and seqtag_run:
        _warn_mismatch(
            model,
            "collapse/run consensus_sequences",
            _count(collapse_run, "consensus_sequences"),
            "seqtag/run input_sequences",
            _count(seqtag_run, "input_sequences"),
        )

    for airr_record in model.records_for("airr"):
        if airr_record.scope_type == "locus":
            seqtag_record = seqtag_run
        elif airr_record.scope_type == "sample_locus" and airr_record.sample:
            seqtag_record = _find_record(
                model,
                "seqtag",
                scope_type="sample",
                sample=airr_record.sample,
            )
        else:
            seqtag_record = None

        if seqtag_record is None or airr_record.locus is None:
            continue

        split_count = _seqtag_split_count(
            seqtag_record,
            airr_record.locus,
        )
        if split_count is None:
            split_count = _count(seqtag_record, "matched_sequences")

        _warn_mismatch(
            model,
            (
                f"seqtag/{seqtag_record.record_id} "
                f"{airr_record.locus} input"
            ),
            split_count,
            (
                f"airr/{airr_record.record_id} "
                "input_sequences"
            ),
            _count(airr_record, "input_sequences"),
        )


def _atomic_write_summary(
    path: Path,
    model: ReportModel,
    rows: Iterable[SummaryRow],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_path = Path(handle.name)

            # Keeping the existing two-line preamble so 
            # we can keep our current R readers using read_tsv(..., skip = 2).
            handle.write(
                f"LongAIRR version: {_clean_cell(model.longairr_version)}\n"
            )
            handle.write(f"Sample: {_clean_cell(model.run_root)}\n")

            writer = csv.writer(
                handle,
                delimiter="\t",
                lineterminator="\n",
                quoting=csv.QUOTE_MINIMAL,
            )
            writer.writerow(
                [
                    "Step",
                    "PathInfo",
                    "Date",
                    "InputReads",
                    "OutputReads",
                    "PercentRetained",
                    "InputDescription",
                    "OutputDescription",
                ]
            )
            for row in rows:
                writer.writerow(row.as_cells())

            handle.flush()
            os.fsync(handle.fileno())

        os.replace(tmp_path, path)
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink()


# Wrtie summary.tsv
def write_summary_tsv(
    model: ReportModel,
    output_path: str | Path | None = None,
) -> Path:

    if output_path is None:
        path = model.run_root / "summary.tsv"
    else:
        path = Path(output_path).expanduser()
        if not path.is_absolute():
            path = path.resolve()

    rows = build_summary_rows(model)
    if not rows:
        model.warnings.append(
            "No summary rows could be generated from the discovered records."
        )

    _atomic_write_summary(path, model, rows)
    return path



def _html(value: Any) -> str:
    return html_lib.escape(str(value), quote=True)


def _humanize_key(value: str) -> str:
    return value.replace("_", " ").strip().title()


def _format_count(value: int | None) -> str:
    return "—" if value is None else f"{value:,}"


def _format_rate(output_count: int | None, input_count: int | None) -> str:
    if output_count is None or input_count is None or input_count <= 0:
        return "—"
    return f"{output_count * 100.0 / input_count:.1f}%"


def _format_duration(value: float | None) -> str:
    if value is None:
        return "—"
    seconds = int(round(value))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:d}h {minutes:02d}m {seconds:02d}s"
    if minutes:
        return f"{minutes:d}m {seconds:02d}s"
    return f"{seconds:d}s"


def _record_scope_label(record: ModuleRecord) -> str:
    if record.scope_type == "run":
        return "Run"
    if record.scope_type == "sample" and record.sample:
        return f"Sample: {record.sample}"
    if record.scope_type == "locus" and record.locus:
        return f"Locus: {_locus_label(record.locus)}"
    if record.sample and record.locus:
        return f"{record.sample} · {_locus_label(record.locus)}"
    return record.scope_type


def _record_transition(record: ModuleRecord) -> tuple[int | None, int | None, str]:
    if record.module == "filter":
        return _count(record, "input_reads"), _count(record, "filtered_reads"), "Filtered reads"
    if record.module == "collapse":
        return _count(record, "input_reads"), _count(record, "consensus_sequences"), "Consensus sequences"
    if record.module == "seqtag":
        return _count(record, "input_sequences"), _count(record, "matched_sequences"), "Seqtag matches"
    if record.module == "airr":
        productive = _count(record, "productive_sequences")
        if productive is not None:
            return _count(record, "input_sequences"), productive, "Productive sequences"
        return _count(record, "input_sequences"), _count(record, "airr_sequences"), "Valid AIRR sequences"
    values = list(record.counts.values())
    if not values:
        return None, None, "Output"
    return values[0], values[-1], "Output"


def _file_href(value: str) -> str:
    file_path = Path(value).expanduser()
    try:
        if file_path.is_absolute():
            return file_path.as_uri()
    except ValueError:
        pass
    return value


def _file_exists(value: str) -> bool:
    try:
        return Path(value).expanduser().exists()
    except OSError:
        return False


def _metric_card(label: str, value: int | str | None, detail: str) -> str:
    display = (
        f"{value:,}"
        if isinstance(value, int)
        else ("—" if value is None else str(value))
    )
    return (
        '<article class="metric-card">'
        f'<div class="metric-label">{_html(label)}</div>'
        f'<div class="metric-value">{_html(display)}</div>'
        f'<div class="metric-detail">{_html(detail)}</div>'
        '</article>'
    )


def _sum_count(records: Sequence[ModuleRecord], key: str) -> int | None:
    values = [_count(record, key) for record in records]
    available = [value for value in values if value is not None]
    return sum(available) if available else None


def _overview_metrics(model: ReportModel) -> str:
    filter_record = _find_record(model, "filter", scope_type="run")
    collapse_record = _find_record(model, "collapse", scope_type="run")
    seqtag_record = _find_record(model, "seqtag", scope_type="run")
    airr_records = _locus_records(model)
    cards: list[str] = []

    if filter_record:
        raw = _count(filter_record, "input_reads")
        filtered = _count(filter_record, "filtered_reads")
        cards.append(_metric_card("Input reads", raw, "Reads entering filtering"))
        cards.append(
            _metric_card(
                "Filtered reads",
                filtered,
                f"{_format_rate(filtered, raw)} retained",
            )
        )
    elif collapse_record:
        cards.append(
            _metric_card(
                "Collapse input",
                _count(collapse_record, "input_reads"),
                "Reads entering collapse",
            )
        )
    elif seqtag_record:
        cards.append(
            _metric_card(
                "Seqtag input",
                _count(seqtag_record, "input_sequences"),
                "Sequences entering seqtag",
            )
        )

    if collapse_record:
        consensus = _count(collapse_record, "consensus_sequences")
        source = _count(collapse_record, "input_reads")
        cards.append(
            _metric_card(
                "Consensus sequences",
                consensus,
                f"{_format_rate(consensus, source)} of collapse input",
            )
        )

    if seqtag_record:
        matched = _count(seqtag_record, "matched_sequences")
        source = _count(seqtag_record, "input_sequences")
        cards.append(
            _metric_card(
                "Seqtag matches",
                matched,
                f"{_format_rate(matched, source)} of seqtag input",
            )
        )

    productive = _sum_count(airr_records, "productive_sequences")
    if productive is not None:
        airr_input = _sum_count(airr_records, "input_sequences")
        seqtag_matched = (
            _count(seqtag_record, "matched_sequences")
            if seqtag_record
            else None
        )
        if seqtag_matched is not None and airr_input == seqtag_matched:
            denominator = seqtag_matched
            denominator_label = "seqtag matches"
        else:
            denominator = airr_input
            denominator_label = "available AIRR input"

        breakdown = " + ".join(
            f"{_count(record, 'productive_sequences'):,} "
            f"{_locus_label(record.locus or record.record_id)}"
            for record in airr_records
            if _count(record, "productive_sequences") is not None
        )
        detail = f"{_format_rate(productive, denominator)} of {denominator_label}"
        if breakdown:
            detail += f" · {breakdown}"
        cards.append(_metric_card("Productive AIRR", productive, detail))

    if model.records:
        total = sum(record.duration_seconds or 0.0 for record in model.records)
        cards.append(
            _metric_card(
                "LongAIRR runtime",
                _format_duration(total),
                f"{len(model.records)} module record(s)",
            )
        )

    if not cards:
        return '<div class="empty">No overview metrics available.</div>'
    return '<div class="metric-grid">' + ''.join(cards) + '</div>'


def _status_badge(status: str) -> str:
    return (
        f'<span class="status status-{_html(status)}">'
        f'{_html(status.title())}</span>'
    )


def _validation_badge(model: ReportModel) -> str:
    if model.warnings:
        return (
            '<span class="validation-chip warning">'
            f'{len(model.warnings)} validation warning(s)</span>'
        )
    return '<span class="validation-chip success">Validation passed</span>'


def _warnings_section(model: ReportModel) -> str:
    if not model.warnings:
        return ""
    items = ''.join(f'<li>{_html(item)}</li>' for item in model.warnings)
    return (
        '<article class="section warning-section">'
        '<h2>Validation warnings</h2>'
        '<p class="desc">The report was generated, but these metadata '
        'relationships should be reviewed.</p>'
        f'<div class="notice warning"><ul>{items}</ul></div>'
        '</article>'
    )


def _module_summary_table(model: ReportModel) -> str:
    rows: list[str] = []
    for record in model.records:
        input_count, output_count, output_label = _record_transition(record)
        rows.append(
            '<tr>'
            f'<td><strong>{_html(record.module.title())}</strong>'
            f'<div class="subtle">{_html(record.record_id)}</div></td>'
            f'<td>{_html(_record_scope_label(record))}</td>'
            f'<td>{_status_badge(record.status)}</td>'
            f'<td class="num">{_html(_format_count(input_count))}</td>'
            f'<td class="num">{_html(_format_count(output_count))}'
            f'<div class="subtle">{_html(output_label)}</div></td>'
            f'<td class="num">{_html(_format_rate(output_count, input_count))}</td>'
            f'<td>{_html(_format_duration(record.duration_seconds))}</td>'
            f'<td>{_html(_format_date(record.finished_at))}</td>'
            '</tr>'
        )
    if not rows:
        rows.append('<tr><td colspan="8" class="empty">No module records found.</td></tr>')
    return (
        '<div class="table-wrap"><table><thead><tr>'
        #'<th>Module</th><th>Scope</th><th>Status</th><th>Input</th>'
        #'<th>Output</th><th>Retention</th><th>Runtime</th><th>Finished</th>'
        '<th>Module</th><th>Scope</th><th>Status</th>'
        '<th class="num">Input</th>'
        '<th class="num">Output</th>'
        '<th class="num">Retention</th>'
        '<th>Runtime</th><th>Finished</th>'
        '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'
    )


def _append_stage(
    stages: list[tuple[str, int, str]],
    label: str,
    value: int | None,
    note: str = "",
) -> None:
    if value is None:
        return
    if stages and stages[-1][0] == label and stages[-1][1] == value:
        return
    stages.append((label, value, note))


def _read_retention_stages(model: ReportModel) -> list[tuple[str, int, str]]:
    filter_record = _find_record(model, "filter", scope_type="run")
    collapse_record = _find_record(model, "collapse", scope_type="run")
    stages: list[tuple[str, int, str]] = []

    if filter_record:
        _append_stage(stages, "Input reads", _count(filter_record, "input_reads"))
        _append_stage(
            stages,
            "Filtered reads",
            _count(filter_record, "filtered_reads"),
        )

    if collapse_record:
        collapse_input = _count(collapse_record, "input_reads")
        if not stages or stages[-1][1] != collapse_input:
            _append_stage(stages, "Collapse input", collapse_input)
        _append_stage(
            stages,
            "SPBC/UMI annotated",
            _count(collapse_record, "annotated_reads"),
        )
        _append_stage(
            stages,
            "Fixed-length filtered",
            _count(collapse_record, "length_filtered_reads"),
        )
        _append_stage(
            stages,
            "AF-retained group reads",
            _count(collapse_record, "retained_group_reads"),
        )

    return stages


def _yield_retention_stages(model: ReportModel) -> list[tuple[str, int, str]]:
    collapse_record = _find_record(model, "collapse", scope_type="run")
    seqtag_record = _find_record(model, "seqtag", scope_type="run")
    airr_records = _locus_records(model)
    stages: list[tuple[str, int, str]] = []

    if collapse_record:
        _append_stage(
            stages,
            "Consensus sequences",
            _count(collapse_record, "consensus_sequences"),
        )

    if seqtag_record:
        seqtag_input = _count(seqtag_record, "input_sequences")
        if not stages or stages[-1][1] != seqtag_input:
            _append_stage(stages, "Seqtag input", seqtag_input)
        _append_stage(
            stages,
            "Seqtag matches",
            _count(seqtag_record, "matched_sequences"),
        )

    if airr_records:
        airr_input = _sum_count(airr_records, "input_sequences")
        if not stages or stages[-1][1] != airr_input:
            loci = ", ".join(
                _locus_label(record.locus or record.record_id)
                for record in airr_records
            )
            _append_stage(
                stages,
                "AIRR input represented",
                airr_input,
                f"Available loci: {loci}",
            )
        _append_stage(
            stages,
            "Valid AIRR sequences",
            _sum_count(airr_records, "airr_sequences"),
        )
        _append_stage(
            stages,
            "Productive AIRR sequences",
            _sum_count(airr_records, "productive_sequences"),
        )

    return stages


def _retention_panel(
    stages: Sequence[tuple[str, int, str]],
    *,
    unit_label: str,
) -> str:
    if not stages:
        return '<div class="empty">No retention stages available for this run.</div>'

    initial = stages[0][1]
    scale = max((value for _, value, _ in stages), default=0) or 1
    bars: list[str] = []
    rows: list[str] = []

    previous: int | None = None
    for label, value, note in stages:
        width = max(0.0, min(100.0, value * 100.0 / scale))
        previous_rate = _format_rate(value, previous) if previous is not None else "—"
        initial_rate = _format_rate(value, initial)
        note_html = f'<div class="subtle">{_html(note)}</div>' if note else ""
        bars.append(
            '<div class="retention-row">'
            f'<div class="retention-label"><strong>{_html(label)}</strong>{note_html}</div>'
            '<div class="retention-track">'
            f'<div class="retention-bar" style="width:{width:.2f}%"></div>'
            '</div>'
            f'<div class="retention-count">{value:,}</div>'
            '</div>'
        )
        rows.append(
            '<tr>'
            f'<td>{_html(label)}{note_html}</td>'
            f'<td class="num">{value:,}</td>'
            f'<td class="num">{_html(previous_rate)}</td>'
            f'<td class="num">{_html(initial_rate)}</td>'
            '</tr>'
        )
        previous = value

    return (
        '<div class="retention-chart">' + ''.join(bars) + '</div>'
        '<div class="table-wrap retention-table"><table><thead><tr>'
        #f'<th>Stage</th><th>{_html(unit_label)}</th>'
        #'<th>% of previous</th><th>% of first available stage</th>'
        f'<th>Stage</th><th class="num">{_html(unit_label)}</th>'
        '<th class="num">% of previous</th>'
        '<th class="num">% of first available stage</th>'   
        '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'
    )


def _summary_html_table(model: ReportModel) -> str:
    rows = build_summary_rows(model)
    body = ''.join(
        '<tr>'
        f'<td>{_html(row.step)}</td><td>{_html(row.path_info)}</td>'
        f'<td>{_html(row.date)}</td>'
        f'<td class="num">{row.input_reads:,}</td>'
        f'<td class="num">{row.output_reads:,}</td>'
        f'<td class="num">{_html(row.as_cells()[5] or "—")}</td>'
        f'<td>{_html(row.input_description)}</td>'
        f'<td>{_html(row.output_description)}</td>'
        '</tr>'
        for row in rows
    )
    if not body:
        body = '<tr><td colspan="8" class="empty">No summary rows available.</td></tr>'
    return (
        '<div class="table-wrap"><table><thead><tr>'
        '<th>Step</th><th>Path info</th><th>Date</th><th>Input</th>'
        '<th>Output</th><th>Retained</th><th>Input description</th>'
        '<th>Output description</th></tr></thead><tbody>'
        + body + '</tbody></table></div>'
    )


def _locus_records(model: ReportModel) -> list[ModuleRecord]:
    return sorted(
        [record for record in model.records_for("airr") if record.locus],
        key=lambda record: (
            record.sample or "",
            LOCUS_ORDER.get(record.locus or "", 100),
            record.locus or "",
        ),
    )


def _loci_table(model: ReportModel) -> str:
    rows: list[str] = []
    for record in _locus_records(model):
        source = _count(record, "input_sequences")
        valid = _count(record, "airr_sequences")
        productive = _count(record, "productive_sequences")
        heavy = _count(record, "productive_heavy_sequences")
        label = _locus_label(record.locus or record.record_id)
        sample_html = (
            f'<div class="subtle">{_html(record.sample)}</div>'
            if record.sample
            else ""
        )
        rows.append(
            '<tr>'
            f'<td><strong>{_html(label)}</strong>{sample_html}</td>'
            f'<td class="num">{_html(_format_count(source))}</td>'
            f'<td class="num">{_html(_format_count(valid))}</td>'
            f'<td class="num">{_html(_format_rate(valid, source))}</td>'
            f'<td class="num">{_html(_format_count(productive))}</td>'
            f'<td class="num">{_html(_format_rate(productive, valid))}</td>'
            f'<td class="num">{_html(_format_count(heavy))}</td>'
            '</tr>'
        )
    if not rows:
        rows.append('<tr><td colspan="7" class="empty">No locus-level AIRR records available.</td></tr>')
    return (
        '<div class="table-wrap"><table><thead><tr>'
        #'<th>Locus</th><th>Input</th><th>Valid AIRR</th>'
        #'<th>Annotation rate</th><th>Productive</th>'
        #'<th>Productive rate</th><th>Productive heavy</th>'
        '<th>Locus</th>'
        '<th class="num">Input</th>'
        '<th class="num">Valid AIRR</th>'
        '<th class="num">Annotation rate</th>'
        '<th class="num">Productive</th>'
        '<th class="num">Productive rate</th>'
        '<th class="num">Productive heavy</th>'
        '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'
    )


def _locus_outcomes_chart(model: ReportModel) -> str:
    records = _locus_records(model)
    if not records:
        return '<div class="empty">No locus outcome data available.</div>'

    chart_rows: list[str] = []
    legend_classes: set[str] = set()
    for record in records:
        source = _count(record, "input_sequences")
        valid = _count(record, "airr_sequences")
        productive = _count(record, "productive_sequences")
        heavy = _count(record, "productive_heavy_sequences")
        if source is None or source <= 0 or valid is None:
            continue

        unannotated = max(source - valid, 0)
        segments: list[tuple[str, int, str]] = []
        if productive is not None:
            nonproductive = max(valid - productive, 0)
            segments.extend([
                ("Productive", productive, "productive"),
                ("Valid, nonproductive", nonproductive, "nonproductive"),
            ])
        else:
            segments.append(("Valid AIRR", valid, "valid"))
        segments.append(("No valid V(D)J", unannotated, "unannotated"))

        segment_html: list[str] = []
        counts_html: list[str] = []
        for label, value, css_class in segments:
            legend_classes.add(css_class)
            width = max(0.0, min(100.0, value * 100.0 / source))
            segment_html.append(
                f'<div class="outcome-segment {css_class}" '
                f'style="width:{width:.4f}%" '
                f'title="{_html(label)}: {value:,} ({width:.1f}%)"></div>'
            )
            counts_html.append(
                f'<span><i class="legend-dot {css_class}"></i>'
                f'{_html(label)}: <strong>{value:,}</strong></span>'
            )

        label = _locus_label(record.locus or record.record_id)
        if record.sample:
            label = f"{record.sample} · {label}"
        heavy_html = (
            f'<div class="subtle">Productive heavy-chain subset: {heavy:,}</div>'
            if heavy is not None
            else ""
        )
        chart_rows.append(
            '<div class="outcome-row">'
            f'<div class="outcome-label"><strong>{_html(label)}</strong>'
            f'<div class="subtle">Input: {source:,}</div>{heavy_html}</div>'
            '<div class="outcome-main">'
            '<div class="outcome-bar">' + ''.join(segment_html) + '</div>'
            '<div class="outcome-counts">' + ''.join(counts_html) + '</div>'
            '</div></div>'
        )

    if not chart_rows:
        return '<div class="empty">No complete locus outcome counts available.</div>'
    return '<div class="outcome-chart">' + ''.join(chart_rows) + '</div>'


PARAMETER_FLAGS: dict[str, dict[str, str]] = {
    "filter": {
        "min_quality": "--min-qual",
        "min_length": "--minl",
        "max_length": "--maxl",
    },
    "collapse": {
        "library": "--library",
        "demux": "--demux",
        "window_length": "--window-length",
        "anchor_error": "--anchor-error",
        "umi_length": "--umi-length",
        "spbc_error": "--spbc-error",
        "spbc_length": "--spbc-length",
        "min_length": "--minl",
        "max_length": "--maxl",
        "group_field": "--group-field",
        "adaptive_filter": "--adaptive-filter",
        "min_group_size": "--filter-min-size",
        "bin_size": "--bin-size",
        "peak_margin": "--peak-margin",
        "consensus_max_gap": "--cons-gap",
        "consensus_max_error": "--cons-error",
        "max_reads_per_group": "--n-subsample",
        "groups_per_chunk": "--n-chunk",
        "seed": "--seed",
        "parallel_jobs": "--cjobs",
    },
    "seqtag": {
        "window_length": "--window-length",
        "anchor_error": "--anchor-error",
        "primer_field": "--pf",
        "split": "--split",
        "split_regex": "--split-regex",
    },
    "airr": {
        "locus": "--loci",
        "filter_productive": "--ph",
    },
}


def _format_setting_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _settings_table(rows: Sequence[tuple[str, Any]], empty_text: str) -> str:
    if not rows:
        return f'<div class="empty compact">{_html(empty_text)}</div>'
    body = ''.join(
        '<tr>'
        f'<th><code>{_html(label)}</code></th>'
        f'<td><code>{_html(_format_setting_value(value))}</code></td>'
        '</tr>'
        for label, value in rows
    )
    return '<div class="table-wrap compact"><table class="kv"><tbody>' + body + '</tbody></table></div>'


def _parameter_sections(record: ModuleRecord) -> str:
    flag_map = PARAMETER_FLAGS.get(record.module, {})
    command_rows: list[tuple[str, Any]] = []
    internal_rows: list[tuple[str, Any]] = []

    for key, value in sorted(record.parameters.items()):
        flag = flag_map.get(key)
        if flag:
            command_rows.append((flag, value))
        else:
            internal_rows.append((_humanize_key(key), value))

    sections = [
        '<section><h4>Command parameters</h4>'
        + _settings_table(command_rows, "No user-facing command parameters recorded.")
        + '</section>'
    ]
    if internal_rows:
        sections.append(
            '<section><h4>Internal and fixed settings</h4>'
            + _settings_table(internal_rows, "No internal settings recorded.")
            + '</section>'
        )
    return ''.join(sections)


def _classify_file(record: ModuleRecord, key: str) -> str:
    module = record.module
    lower = key.lower()

    if module == "filter":
        if key == "input_fastq":
            return "inputs"
        if key in {"filtered_fastq", "filtered_fasta"}:
            return "outputs"
        if key in {"log", "nanoplot_report"}:
            return "diagnostics"
    elif module == "collapse":
        if key in {
            "input_anchor",
            "input_sequences",
            "visium_spatial_barcodes",
            "visiumhd_spatial_barcode_index",
        }:
            return "inputs"
        if key == "consensus_fasta":
            return "outputs"
        if key in {"log", "failed_spatial_barcodes", "failed_adaptive_filter"}:
            return "diagnostics"
        if key in {
            "annotated_sequences",
            "length_filtered_sequences",
            "retained_group_sequences",
        }:
            return "intermediates"
    elif module == "seqtag":
        if key in {"input_anchor", "input_sequences"}:
            return "inputs"
        if key.startswith("split_") and key.endswith("_fasta"):
            return "outputs"
        if key == "matched_fasta":
            has_split_outputs = any(
                file_key.startswith("split_") and file_key.endswith("_fasta")
                for file_key in record.files
            )
            return "intermediates" if has_split_outputs else "outputs"
        if key in {"failed_fasta", "log"}:
            return "diagnostics"
    elif module == "airr":
        if key in {"input_sequences", "igblast_database", "germline_database"}:
            return "inputs"
        if key in {"productive_airr_tsv", "productive_heavy_airr_tsv"}:
            return "outputs"
        if key == "airr_tsv":
            return (
                "intermediates"
                if "productive_airr_tsv" in record.files
                else "outputs"
            )
        if key == "log":
            return "diagnostics"
        if key == "igblast_fmt7":
            return "intermediates"

    if lower.startswith("input_"):
        return "inputs"
    if "log" in lower or "qc" in lower or "failed" in lower or "nanoplot" in lower:
        return "diagnostics"
    return "other"


def _file_rows(files: Sequence[tuple[str, str]]) -> str:
    if not files:
        return '<div class="empty compact">No files recorded.</div>'
    rows: list[str] = []
    for key, value in files:
        badge = (
            '<span class="file-badge present">Present</span>'
            if _file_exists(value)
            else '<span class="file-badge missing">Not found</span>'
        )
        rows.append(
            '<tr>'
            f'<th>{_html(_humanize_key(key))}</th>'
            f'<td><a href="{_html(_file_href(value))}">'
            f'<code>{_html(value)}</code></a>{badge}</td>'
            '</tr>'
        )
    return '<div class="table-wrap compact"><table class="kv"><tbody>' + ''.join(rows) + '</tbody></table></div>'


def _file_sections(record: ModuleRecord) -> str:
    groups: dict[str, list[tuple[str, str]]] = {
        "inputs": [],
        "outputs": [],
        "diagnostics": [],
        "intermediates": [],
        "other": [],
    }
    for key, value in sorted(record.files.items()):
        groups[_classify_file(record, key)].append((key, value))

    sections: list[str] = []
    for group_key, title in (
        ("inputs", "Inputs"),
        ("outputs", "Main outputs"),
        ("diagnostics", "Diagnostics and QC"),
    ):
        if groups[group_key]:
            sections.append(
                f'<section><h4>{_html(title)}</h4>'
                f'{_file_rows(groups[group_key])}</section>'
            )

    if groups["intermediates"]:
        sections.append(
            '<details class="sub-detail"><summary>Intermediate files '
            f'({len(groups["intermediates"])})</summary>'
            f'{_file_rows(groups["intermediates"])}</details>'
        )
    if groups["other"]:
        sections.append(
            '<details class="sub-detail"><summary>Other recorded files '
            f'({len(groups["other"])})</summary>'
            f'{_file_rows(groups["other"])}</details>'
        )
    return ''.join(sections) or '<div class="empty compact">No files recorded.</div>'


def _counts_table(record: ModuleRecord) -> str:
    rows = [(_humanize_key(key), value) for key, value in sorted(record.counts.items())]
    return _settings_table(rows, "No counts recorded.")


def _record_details(model: ReportModel) -> str:
    details: list[str] = []
    for record in model.records:
        metadata_rows = [
            ("Scope", dict(record.scope)),
            ("Started at", record.started_at),
            ("Finished at", record.finished_at),
            ("Source JSON", str(record.source_path)),
        ]
        details.append(
            '<details class="record-detail">'
            '<summary>'
            f'<span class="record-title">{_html(record.module.title())} · '
            f'{_html(record.record_id)}</span>'
            f'<span class="record-scope">{_html(_record_scope_label(record))}</span>'
            f'{_status_badge(record.status)}'
            f'<span class="record-runtime">{_html(_format_duration(record.duration_seconds))}</span>'
            '</summary>'
            '<div class="record-body">'
            '<div class="detail-grid">'
            f'<section><h4>Counts</h4>{_counts_table(record)}</section>'
            f'{_parameter_sections(record)}'
            '</div>'
            '<div class="file-section-grid">'
            f'{_file_sections(record)}'
            '</div>'
            '<details class="sub-detail"><summary>Record metadata</summary>'
            f'{_settings_table(metadata_rows, "No record metadata.")}'
            '</details>'
            '</div></details>'
        )
    return ''.join(details) if details else '<div class="empty">No module records available.</div>'


def _qc_links(model: ReportModel) -> str:
    links: list[str] = []
    seen: set[str] = set()
    for record in model.records:
        for key, value in record.files.items():
            lower_key = key.lower()
            lower_value = value.lower()
            if (
                "nanoplot" in lower_key
                or "nanoplot" in lower_value
                or lower_key.endswith("_html")
                or lower_value.endswith(".html")
            ):
                if value in seen:
                    continue
                seen.add(value)
                links.append(
                    f'<a class="resource" href="{_html(_file_href(value))}">'
                    f'<span>{_html(record.module.title())}</span>'
                    f'<strong>{_html(_humanize_key(key))}</strong>'
                    f'<small>{_html(value)}</small></a>'
                )
    if not links:
        return '<div class="empty compact">No linked QC HTML reports were recorded.</div>'
    return '<div class="resource-grid">' + ''.join(links) + '</div>'


def _find_logo_path() -> Path | None:
    candidates: list[Path] = []
    configured = os.environ.get("LONGAIRR_LOGO")
    if configured:
        candidates.append(Path(configured).expanduser())

    script_dir = Path(__file__).resolve().parent
    candidates.extend([
        script_dir / "longairr_logo.png",
        script_dir.parent / "vignette" / "figures" / "longairr_logo.png",
        script_dir.parent.parent / "vignette" / "figures" / "longairr_logo.png",
        Path.cwd() / "vignette" / "figures" / "longairr_logo.png",
    ])

    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


def _logo_data_uri() -> str | None:
    logo_path = _find_logo_path()
    if logo_path is None:
        return None
    try:
        encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    except OSError:
        return None
    return f"data:image/png;base64,{encoded}"


def render_html_report(model: ReportModel) -> str:
    generated = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    run_name = model.run_root.name or str(model.run_root)
    logo_uri = _logo_data_uri()
    logo_html = (
        '<div class="hero-logo-wrap">'
        f'<img class="hero-logo" src="{_html(logo_uri)}" alt="LongAIRR logo">'
        '</div>'
        if logo_uri
        else ""
    )

    css = r'''
:root{--bg:#f4f7fb;--surface:#fff;--soft:#f8fafc;--ink:#142033;--muted:#66758a;--line:#dce4ee;--accent:#285e9a;--accent2:#173f70;--success:#237a57;--successbg:#e9f7f0;--warning:#9a6418;--warningbg:#fff6df;--danger:#a13b3b;--dangerbg:#fdeeee;--productive:#2b8a62;--nonproductive:#d18a2e;--valid:#3b78b8;--unannotated:#cbd5e1;--shadow:0 14px 36px rgba(30,54,83,.08)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.5}a{color:var(--accent2)}code{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;overflow-wrap:anywhere}.shell{max-width:1480px;margin:auto;padding:28px}.hero{background:linear-gradient(135deg,#173f70,#285e9a 58%,#3b7bbb);color:#fff;padding:34px;border-radius:22px;box-shadow:var(--shadow)}.hero-content{display:flex;gap:28px;align-items:center;justify-content:space-between}.hero-copy{min-width:0;flex:1}.hero-logo-wrap{flex:0 0 auto;background:transparent;border-radius:0;padding:0;box-shadow:none;}.hero-logo{display:block;width:224px;height:auto;object-fit:contain;}.kicker{margin:0 0 8px;font-size:.78rem;font-weight:750;letter-spacing:.16em;text-transform:uppercase;opacity:.78}.hero h1{margin:0;font-size:clamp(2rem,4vw,3.2rem);line-height:1.05}.subtitle{max-width:980px;margin:14px 0 0;font-size:1rem;opacity:.88;overflow-wrap:anywhere}.meta{display:flex;flex-wrap:wrap;align-items:center;gap:10px 22px;margin-top:24px;font-size:.88rem;opacity:.9}.validation-chip{display:inline-flex;border-radius:999px;padding:5px 10px;font-weight:760}.validation-chip.success{color:#dff8eb;background:rgba(23,112,75,.48)}.validation-chip.warning{color:#fff2ca;background:rgba(153,95,12,.5)}.tabs{display:flex;gap:8px;margin-top:22px;padding:7px;background:rgba(255,255,255,.13);border-radius:14px;width:fit-content}.tab{border:0;border-radius:10px;padding:10px 16px;cursor:pointer;color:#fff;background:transparent;font:inherit;font-weight:700}.tab.active{background:#fff;color:var(--accent2)}.panel{display:none}.panel.active{display:block}.section{margin-top:22px;background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:24px;box-shadow:var(--shadow)}.section h2{margin:0 0 3px;font-size:1.35rem}.section h4{margin:0 0 10px}.desc{margin:0 0 18px;color:var(--muted);font-size:.93rem}.metric-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin-top:22px}.metric-card{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:18px;box-shadow:var(--shadow)}.metric-label{color:var(--muted);font-size:.82rem;font-weight:750;text-transform:uppercase;letter-spacing:.05em}.metric-value{margin-top:7px;font-size:1.9rem;font-weight:780;letter-spacing:-.03em}.metric-detail{margin-top:3px;color:var(--muted);font-size:.85rem}.table-wrap{width:100%;overflow-x:auto;border:1px solid var(--line);border-radius:13px}.table-wrap.compact{border-radius:10px}table{width:100%;border-collapse:collapse;background:var(--surface)}th,td{padding:12px 13px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}thead th{background:var(--soft);color:var(--muted);font-size:.76rem;text-transform:uppercase;letter-spacing:.05em}tbody tr:last-child td,tbody tr:last-child th{border-bottom:0}.num{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}.subtle{margin-top:2px;color:var(--muted);font-size:.78rem}.status,.file-badge{display:inline-flex;border-radius:999px;padding:3px 8px;font-size:.72rem;font-weight:760;white-space:nowrap}.status-success,.file-badge.present{color:var(--success);background:var(--successbg)}.status-failed,.file-badge.missing{color:var(--danger);background:var(--dangerbg)}.status-skipped{color:var(--warning);background:var(--warningbg)}.file-badge{margin-left:8px}.notice{border-radius:13px;padding:15px 17px;border:1px solid}.notice.warning{color:var(--warning);background:var(--warningbg);border-color:#ecd59f}.notice ul{margin:0}.empty{padding:28px;color:var(--muted);text-align:center}.empty.compact{padding:12px}.retention-chart{display:flex;flex-direction:column;gap:12px;margin-bottom:18px}.retention-row{display:grid;grid-template-columns:minmax(180px,260px) minmax(180px,1fr) 90px;gap:14px;align-items:center}.retention-label{font-size:.9rem}.retention-track{height:24px;border-radius:999px;background:#e9eef5;overflow:hidden}.retention-bar{height:100%;min-width:2px;border-radius:999px;background:linear-gradient(90deg,var(--accent2),var(--accent))}.retention-count{text-align:right;font-weight:760;font-variant-numeric:tabular-nums}.retention-table{margin-top:6px}.outcome-chart{display:flex;flex-direction:column;gap:22px}.outcome-row{display:grid;grid-template-columns:minmax(190px,260px) 1fr;gap:18px;align-items:center}.outcome-bar{display:flex;height:34px;border-radius:10px;overflow:hidden;background:#edf2f7}.outcome-segment{height:100%}.outcome-segment.productive,.legend-dot.productive{background:var(--productive)}.outcome-segment.nonproductive,.legend-dot.nonproductive{background:var(--nonproductive)}.outcome-segment.valid,.legend-dot.valid{background:var(--valid)}.outcome-segment.unannotated,.legend-dot.unannotated{background:var(--unannotated)}.outcome-counts{display:flex;flex-wrap:wrap;gap:7px 18px;margin-top:8px;color:var(--muted);font-size:.83rem}.legend-dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px}.resource-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}.resource{display:flex;flex-direction:column;gap:3px;color:inherit;text-decoration:none;border:1px solid var(--line);border-radius:13px;padding:14px;background:var(--soft)}.resource span{color:var(--muted);font-size:.75rem;text-transform:uppercase;font-weight:750}.resource small{color:var(--muted);overflow-wrap:anywhere}.collapsible-section{padding:0;overflow:hidden}.collapsible-section>summary{cursor:pointer;list-style:none;padding:22px 24px;font-weight:780}.collapsible-section>summary::-webkit-details-marker{display:none}.collapsible-section>summary:after{content:"+";float:right;color:var(--accent)}.collapsible-section[open]>summary:after{content:"−"}.collapsible-content{padding:0 24px 24px}.record-detail{background:var(--surface);border:1px solid var(--line);border-radius:13px;margin-bottom:12px;overflow:hidden}.record-detail summary{display:grid;grid-template-columns:minmax(170px,1fr) minmax(130px,auto) auto auto;gap:12px;align-items:center;cursor:pointer;padding:15px 17px;background:var(--soft)}.record-detail[open]>summary{border-bottom:1px solid var(--line)}.record-title{font-weight:780}.record-scope,.record-runtime{color:var(--muted);font-size:.84rem}.record-body{padding:18px}.detail-grid{display:grid;grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr);gap:18px}.file-section-grid>section{margin-top:18px}.sub-detail{margin-top:16px;border:1px solid var(--line);border-radius:11px;overflow:hidden}.sub-detail>summary{cursor:pointer;background:var(--soft);padding:12px 14px;font-weight:720}.sub-detail>.table-wrap{border:0;border-top:1px solid var(--line);border-radius:0}.kv th{width:220px;color:var(--muted);background:var(--soft)}.kv td{overflow-wrap:anywhere}.footer{padding:26px 6px 10px;color:var(--muted);font-size:.82rem;text-align:center}
@media(max-width:900px){.shell{padding:14px}.hero{padding:24px;border-radius:16px}.hero-logo{width:160px;height:auto}.detail-grid{grid-template-columns:1fr}.record-detail summary{grid-template-columns:1fr auto}.record-scope,.record-runtime{display:none}.retention-row,.outcome-row{grid-template-columns:1fr}.retention-count{text-align:left}.outcome-label{margin-bottom:-8px}}
@media(max-width:600px){.hero-content{align-items:flex-start}.hero-logo-wrap{display:none}.tabs{width:100%;overflow-x:auto}.tab{white-space:nowrap}}
@media print{body{background:#fff}.shell{max-width:none;padding:0}.hero,.section,.metric-card{box-shadow:none}.tabs{display:none}.panel{display:block!important}.section{break-inside:avoid}a{color:inherit;text-decoration:none}.collapsible-section>.collapsible-content{display:block}.record-detail{break-inside:avoid}}
'''
    js = r'''
document.querySelectorAll(".tab").forEach((button)=>{button.addEventListener("click",()=>{const target=button.dataset.tab;document.querySelectorAll(".tab").forEach((item)=>{item.classList.toggle("active",item===button);item.setAttribute("aria-selected",item===button?"true":"false")});document.querySelectorAll(".panel").forEach((panel)=>panel.classList.toggle("active",panel.id===target))})});
'''

    return f'''<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LongAIRR report · {_html(run_name)}</title><style>{css}</style></head>
<body><main class="shell">
<header class="hero"><div class="hero-content"><div class="hero-copy">
<p class="kicker">LongAIRR Run report</p><h1>{_html(run_name)}</h1>
<p class="subtitle">{_html(model.run_root)}</p>
<div class="meta"><span><strong>Version:</strong> {_html(model.longairr_version)}</span>
<span><strong>Run ID:</strong> {_html(model.run_id)}</span>
<span><strong>Generated:</strong> {_html(generated)}</span>
<span><strong>Records:</strong> {len(model.records)}</span>{_validation_badge(model)}</div>
<nav class="tabs" aria-label="Report sections">
<button class="tab active" data-tab="overview" aria-selected="true">Overview</button>
<button class="tab" data-tab="loci" aria-selected="false">Loci</button>
<button class="tab" data-tab="details" aria-selected="false">Run details</button>
</nav></div>{logo_html}</div></header>

<section id="overview" class="panel active">
{_overview_metrics(model)}
{_warnings_section(model)}
<article class="section"><h2>Module summary</h2><p class="desc"></p>{_module_summary_table(model)}</article>
<article class="section"><h2>Read processing retention</h2><p class="desc"></p>{_retention_panel(_read_retention_stages(model), unit_label="Reads")}</article>
<article class="section"><h2>Consensus and receptor yield</h2><p class="desc"></p>{_retention_panel(_yield_retention_stages(model), unit_label="Sequences")}</article>
<article class="section"><h2>QC reports</h2><p class="desc">Available NanoPlot-reports found in the result directory</p>{_qc_links(model)}</article>
<details class="section collapsible-section"><summary>Full processing table</summary><div class="collapsible-content"><p class="desc"></p>{_summary_html_table(model)}</div></details>
</section>

<section id="loci" class="panel">
<article class="section"><h2>Locus results</h2><p class="desc"></p>{_loci_table(model)}</article>
<article class="section"><h2>Receptor composition details</h2><p class="desc"></p>{_locus_outcomes_chart(model)}</article>
</section>

<section id="details" class="panel">
<article class="section"><h2>Run details</h2><p class="desc">Used parameters, input / output / intermediate files, logs and runtime information.</p>{_record_details(model)}</article>
</section>
<footer class="footer">-Generated locally by LongAIRR-</footer>
</main><script>{js}</script></body></html>'''


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink()


def write_html_report(model: ReportModel, output_path: str | Path | None = None) -> Path:
    if output_path is None:
        output = model.run_root / "longairr_report.html"
    else:
        output = Path(output_path).expanduser()
        if not output.is_absolute():
            output = output.resolve()
    _atomic_write_text(output, render_html_report(model))
    return output



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate LongAIRR module metadata and generate summary.tsv "
            "plus a self-contained HTML report."
        )
    )
    parser.add_argument(
        "run_root",
        help="LongAIRR run root containing .longairr/run.json",
    )
    parser.add_argument(
        "--summary-output",
        help="Output path for summary.tsv (default: RUN_ROOT/summary.tsv)",
    )
    parser.add_argument(
        "--html-output",
        help=(
            "Output path for the HTML report "
            "(default: RUN_ROOT/longairr_report.html)"
        ),
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Do not write summary.tsv.",
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Do not write the HTML report.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat count-consistency warnings as errors.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate and normalize metadata without writing report files.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress success messages; warnings are still printed.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.validate_only and args.no_summary and args.no_html:
        parser.error(
            "--no-summary and --no-html cannot be used together unless "
            "--validate-only is specified."
        )

    try:
        model = load_report_model(args.run_root)

        if args.strict and model.warnings:
            warning_text = "\n".join(f"- {item}" for item in model.warnings)
            raise ReportError(
                "Strict validation failed because warnings were found:\n"
                f"{warning_text}"
            )

        outputs: list[Path] = []
        if not args.validate_only:
            if not args.no_summary:
                outputs.append(
                    write_summary_tsv(
                        model,
                        output_path=args.summary_output,
                    )
                )
            if not args.no_html:
                outputs.append(
                    write_html_report(
                        model,
                        output_path=args.html_output,
                    )
                )

        for warning in model.warnings:
            print(f"WARNING: {warning}", file=sys.stderr)

        if not args.quiet:
            if args.validate_only:
                print(
                    f"Validated {len(model.records)} metadata record(s) "
                    f"for run {model.run_id}."
                )
            else:
                for output in outputs:
                    print(output)

        return 0
    except (OSError, ReportError) as exc:
        parser.error(str(exc))

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
