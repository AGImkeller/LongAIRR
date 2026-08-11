# LongAIRR report module

`longairr report` combines structured metadata written by the preceding
modules into a run-level count summary and HTML report.

Run this module after all requested AIRR analyses have completed.

## How it works

LongAIRR stores module parameters, counts and relevant file paths under the
hidden `.longairr/` directory. The report module validates these records,
checks count relationships and reconstructs the spatial or sample-level
workflow represented by the run.

The report can be generated again after a complete result directory has been
moved or copied.

The run root contains:

```text
.longairr/
├── run.json
└── metadata/
    ├── filter/
    ├── demux/
    ├── collapse/
    ├── seqtag/
    └── airr/
```

Metadata records contain:

- LongAIRR version;
- module and sample/locus scope;
- start and finish times;
- relevant parameters;
- read or sequence counts;
- input, output, and log paths.


## Usage

```text
longairr report [OPTIONS] run_root
```

| Argument | Description |
| --- | --- |
| `run_root` | LongAIRR run root containing `.longairr/run.json` |

## Main options

| Option | Description |
| --- | --- |
| `--summary-output PATH` | Write the TSV summary to a custom path |
| `--html-output PATH` | Write the HTML report to a custom path |
| `--no-summary` | Do not write `summary.tsv` |
| `--no-html` | Do not write the HTML report |
| `--strict` | Treat count-consistency warnings as errors |
| `--validate-only` | Validate metadata without writing reports |
| `--quiet` | Suppress success messages while retaining warnings |

## Generate the report

```bash
longairr report /path/to/longairr_results/
```

Default outputs:

```text
longairr_results/
├── summary.tsv
├── longairr_report.html
└── .longairr/
```

`summary.tsv` provides the main read and sequence counts in a machine-readable
format. `longairr_report.html` presents the workflow, parameters, counts,
warnings and output-file links in a portable report.


!!! info "See also"
    Find an exemplary [HTML report](../../vignettes/longairr_report.html) provided in the repository.

    Underlying file paths will break, since the report is disconnected from its
    corresponding results directory.

    Also listed here: [**Expected output**](../inputs_outputs/output_files.md)
