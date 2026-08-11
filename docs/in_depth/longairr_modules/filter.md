# LongAIRR Filter module

`longairr filter` applies read-quality and length thresholds to a FASTQ file.
It writes filtered FASTQ and FASTA files and generates a NanoPlot report for
the retained reads.

The FASTA output is used by the following LongAIRR modules.

## How it works

Reads are filtered with SeqKit according to the selected minimum quality,
minimum length and maximum length. Setting a threshold to `-1` disables the
corresponding filter.

The retained FASTQ is converted to FASTA, and the input and retained read
counts are recorded in the LongAIRR run metadata.

## Usage

```text
longairr filter [OPTIONS] input_fastq outdir
```

| Argument | Description |
| --- | --- |
| `input_fastq` | Basecalled reads in FASTQ format |
| `outdir` | Existing LongAIRR output directory |

!!! important
    The positional input and output arguments are order-sensitive.

## Main options

| Option | Description | Default |
| --- | --- | --- |
| `--min-qual` | Minimum read quality | No filtering |
| `--minl` | Minimum read length | No filtering |
| `--maxl` | Maximum read length | No filtering |
| `--run-root` | Explicit run root for structured metadata | Auto-detected |

## Example

```bash
longairr filter \
  --min-qual 17 \
  --minl 420 \
  --maxl 6000 \
  input.fastq \
  /path/to/longairr_results/
```

Thresholds should be chosen for the sequencing technology and expected library
insert rather than copied automatically from an example workflow.

## Main outputs

```text
longairr_results/
└── filter_qc/
    ├── longairr_filtered.fastq
    ├── longairr_filtered.fasta
    ├── longairr_filter.log
    └── qc_report/
        └── filtered/
            └── NanoPlot-report.html
```

Use `longairr_filtered.fasta` as input for [`demux`](demux.md) in multiplexed
bulk analyses or directly for [`collapse`](collapse.md) in spatial and
non-multiplexed analyses.
