# LongAIRR basecall module

`longairr basecall` converts Oxford Nanopore POD5 signal data into sequence
reads using [Dorado duplex](https://software-docs.nanoporetech.com/dorado/latest/basecaller/duplex/) basecalling. It can retain simplex reads, duplex reads or both and generates a NanoPlot quality-control report.

This module is only needed when starting from ONT POD5 files. Skip it when
starting from already-basecalled ONT or PacBio HiFi FASTQ files.

## How it works

LongAIRR runs `dorado duplex`, separates reads using the Dorado duplex tag and
writes the selected reads to FASTQ. FASTA output can be generated alongside
the FASTQ files.

If both simplex and duplex reads are selected, they are combined into one file
for downstream processing.

## Requirements

- A directory containing ONT POD5 files
- A compatible Dorado installation available on `PATH`
- A suitable GPU
- A basecalling model name or model path

Basecalling is commonly performed on a dedicated GPU workstation or cluster
node before transferring the resulting FASTQ to the downstream workflow.

## Usage

```text
longairr basecall [OPTIONS] pod5_dir outdir
```

| Argument | Description |
| --- | --- |
| `pod5_dir` | Directory containing ONT POD5 files |
| `outdir` | Existing LongAIRR output directory |

## Main options

| Option | Description | Default |
| --- | --- | --- |
| `-q`, `--min-qual` | Minimum quality passed to Dorado | No limit |
| `--model` | Dorado model name or path | `sup` |
| `--cuda` | GPU device passed to Dorado | `cuda:all` |
| `--batch` | Maximum reads processed by Dorado at once | `64` |
| `--simplex` | Retain simplex reads | `TRUE` |
| `--duplex` | Retain duplex reads | `TRUE` |
| `--fasta` | Also generate FASTA output | `TRUE` |

## Example

```bash
longairr basecall \
  --min-qual 5 \
  --model sup \
  --simplex false \
  --duplex true \
  /path/to/pod5/ \
  /path/to/longairr_results/
```

## Main outputs

The exact sequence files depend on the selected simplex and duplex settings.
For a combined run, the main downstream input is:

```text
longairr_results/
├── basecall/
│   ├── simplex_duplex.fastq
│   ├── simplex_duplex.fasta
│   ├── longairr_basecall.log
│   └── tmp/
│       └── dorado.bam
└── filter_qc/
    └── qc_report/
        └── raw/
            └── NanoPlot-report.html
```

Continue with [`longairr filter`](filter.md) using the generated FASTQ file.

