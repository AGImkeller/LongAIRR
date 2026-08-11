# LongAIRR seqtag module

`longairr seqtag` annotates consensus sequences using supplied sequence
anchors. It can assign constant-region labels or split a combined spatial
library into immunoglobulin and T-cell receptor FASTA files.

Jump to:
[bulk constant-region tagging](#bulk-constant-region-tagging) ·
[spatial-igtr-separation](#spatial-igtr-separation)

## Usage

```text
longairr seqtag [OPTIONS] input_anchor input_seqs outdir
```
!!! important
    The positional input and output arguments are order-sensitive.

## Arguments

| Argument | Description |
| --- | --- |
| `input_anchor` | FASTA containing constant-region or other anchor sequences |
| `input_seqs` | Input consensus sequences in FASTA format |
| `outdir` | Run- or sample-level output directory |

## Options

| Option | Description | Default |
| --- | --- | --- |
| `--window-length` | Sequence window searched for anchors | `220` |
| `--anchor-error` | Maximum anchor mismatch fraction | `0.1` |
| `--pf` | FASTA header field used for the annotation | `ISOTYPE` |
| `--split` | Split passing sequences according to annotations | `FALSE` |
| `--split-regex` | Comma-separated values used to combine/split annotations | Not set |
| `--run-root` | Explicit run root for metadata | Auto-detected |
| `--sample` | Optional sample identifier | Not set |
| `--verbose` | Print runtime information | `TRUE` |

## Anchor FASTA format

Each FASTA header contains the identifier written to the sequence annotation.
For spatial IG/TR separation, identifiers must begin with `Ig` or `TCR`:

```fasta
>Ig | 1 | IGHA
GCATCCCCGACCAGC
>Ig | 5 | IGHM
GGGAGTGCATCCGCC
>TCR | 15 | TRAC
ATCCAGAACCCTGAC
>TCR | 17 | TRBC
AGGTCGCTGTGTTTG
```

The repository contains complete example anchor files under
`longairr_example_workflow/example_inputs/required_anchors/`.

## Bulk constant-region tagging

```bash
longairr seqtag \
  --split false \
  --window-length 220 \
  --anchor-error 0.1 \
  --pf CONSTANT \
  constant_igh_anchors.fasta \
  collapse/4_longairr_consensus.fasta \
  /path/to/sample_results/
```

## Spatial IG/TR separation

```bash
longairr seqtag \
  --split true \
  --split-regex Ig,TCR \
  --window-length 3000 \
  --anchor-error 0.1 \
  --pf ISOTYPE \
  constant_chain_anchors.fasta \
  collapse/4_longairr_consensus.fasta \
  /path/to/results/
```

## Troubleshooting

If few or no reads pass:

- verify that the anchor sequences match the experimental library;
- check the expected read orientation;
- test the reverse-complement anchor where appropriate;
- confirm that `--window-length` spans the expected anchor location.

!!! info "See also"
    Find more information regarding the output files in the [**Expected output**](../inputs_outputs/output_files.md) sections.
