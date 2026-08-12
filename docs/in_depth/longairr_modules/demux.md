# LongAIRR Demux module

`longairr demux` separates compatible multiplexed bulk libraries into
sample-specific FASTA files using supplied unique dual index (UDI) sequences.
It is not used in the spatial workflows.

## How it works

LongAIRR searches each read for a UDI sequence. Reads without a forward match
are reverse-complemented and searched again. Matching reads are combined and
split according to the identifier in the UDI FASTA header.

The resulting sample identifier is used in the downstream `collapse`,
`seqtag`, `airr` and reporting steps.

## UDI FASTA

Provide only the UDI sequences used in the current sequencing run:

```fasta
>UID6
GACGAGAG
>UID20
AGACTTGG
```

The FASTA identifiers must match the sample names used in the bulk Snakemake
configuration.

## Usage

```text
longairr demux [OPTIONS] input_barcodes input_seqs outdir
```

| Argument | Description |
| --- | --- |
| `input_barcodes` | FASTA containing the UDI sequences |
| `input_seqs` | Filtered reads in FASTA format |
| `outdir` | Run-level LongAIRR output directory |

!!! important
    The positional input and output arguments are order-sensitive.

## Main options

| Option | Description | Default |
| --- | --- | --- |
| `--window-length` | Read region searched for a UDI | `50` |
| `--anchor-error` | Maximum allowed UDI mismatch fraction | `0.2` |
| `--run-root` | Explicit run root for structured metadata | Auto-detected |

## Example

```bash
longairr demux \
  --window-length 500 \
  --anchor-error 0.2 \
  /path/to/UDI_barcodes.fasta \
  /path/to/longairr_results/filter_qc/longairr_filtered.fasta \
  /path/to/longairr_results/
```

## Main outputs

```text
longairr_results/
└── sample_demux/
    ├── UID6/
    │   └── split_UDI-UID6.fasta
    ├── UID20/
    │   └── split_UDI-UID20.fasta
    ├── longairr_demux.log
    └── tmp/
```

Continue with [`longairr collapse`](collapse.md) separately for every
demultiplexed sample.

