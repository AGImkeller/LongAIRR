# LongAIRR collapse module

`longairr collapse` annotates UMIs and, for spatial libraries, spatial
barcodes. Reads representing the same original molecule are grouped, aligned
and collapsed into a consensus sequence.

## Usage

```text
longairr collapse [OPTIONS] input_anchor input_seqs outdir
```

Spatial runs additionally require a barcode reference option.

!!! important
    The positional input and output arguments are order-sensitive.

## Positional arguments

| Argument | Description |
| --- | --- |
| `input_anchor` | FASTA containing the anchor used for UMI/barcode annotation |
| `input_seqs` | Input reads in FASTA format |
| `outdir` | Run- or sample-level LongAIRR output directory |

## General options

| Option | Description | Default |
| --- | --- | --- |
| `--demux` | Whether `longairr demux` was performed | `TRUE` |
| `--library` | `bulk`, `visium`, or `visiumhd` | `visium` |
| `--run-root` | Explicit run root for metadata | Auto-detected |
| `--sample` | Sample identifier for demultiplexed bulk data | Not set |
| `--verbose` | Print runtime information | `TRUE` |

## UMI and spatial-barcode options

| Option | Description | Default |
| --- | --- | --- |
| `--window-length` | Anchor-search window | `1200` |
| `--anchor-error` | Maximum anchor mismatch fraction | `0.2` |
| `--umi-length` | UMI length | `12` |
| `--spbc-error` | Maximum spatial-barcode mismatch fraction | `0.0` |
| `--spbc-length` | Visium V1 spatial-barcode length | `16` |
| `--visium-spbc` | Visium V1 coordinate whitelist | Required for `visium` |
| `--hd-spbc-index` | LongAIRR_whitelist SQLite index | Required for `visiumhd` |

The legacy `--hd-spbc1` and `--hd-spbc2` arguments remain in the development
parser but are deprecated by the current Visium HD workflow.

## Filtering and consensus options

| Option | Description | Default |
| --- | --- | --- |
| `--group-field` | FASTA header field used for grouping | Library dependent |
| `--minl` | Minimum read length before consensus | No limit |
| `--maxl` | Maximum read length before consensus | No limit |
| `-f`, `--adaptive-filter` | Enable group-wise adaptive filtering | `TRUE` |
| `-g`, `--filter-min-size` | Minimum group size for adaptive filtering | `5` |
| `--bin-size` | Read-length bin size | `100` |
| `--peak-margin` | Relative margin around the dominant length peak | `0.05` |
| `--cons-gap` | Maximum allowed gap frequency at a consensus position | `0.5` |
| `--cons-error` | Maximum group error rate relative to consensus | `0.2` |
| `--n-subsample` | Maximum reads retained per group before alignment | `999999` |
| `--n-chunk` | Number of groups assigned per alignment chunk | `50` |
| `--seed` | Random seed for subsampling | `1` |
| `--cjobs` | Parallel alignment jobs | `6` |

## Grouping fields

| Library | Allowed/recommended field |
| --- | --- |
| `bulk` | `UMI` |
| `visium` | `SPBCUMI` or `UMI` |
| `visiumhd` | `UMISPBCID` or `UMI` |

Spatial grouping keeps identical UMIs from different tissue positions
separate.

## Adaptive filtering

Adaptive filtering can remove reads with atypical lengths from sufficiently
large groups before multiple-sequence alignment. LongAIRR identifies the
dominant read-length region within each group and retains reads within the
selected margin around that region.

![Adaptive-filtering scheme](../../images_design/images/longairr_af_scheme.png)

The main controls are:

| Option | Function |
| --- | --- |
| `--adaptive-filter` | Enable or disable adaptive filtering |
| `--filter-min-size` | Minimum group size at which adaptive filtering is applied |
| `--bin-size` | Length-bin size used to identify the dominant region |
| `--peak-margin` | Relative margin retained around the dominant region |

Optional fixed `--minl` and `--maxl` thresholds are applied independently of
adaptive filtering.

## Alignment and consensus

Very large groups can be limited with `--n-subsample` before alignment.
`--seed` makes random subsampling reproducible, while `--n-chunk` and
`--cjobs` control how groups are distributed across alignment jobs.

Consensus FASTA headers retain the grouping identifier and read-support
information, including `N_ORIG` and `N_KEEP`. This allows downstream
sequences to be traced back to their original and retained group sizes.

## Main output

```text
collapse/4_longairr_consensus.fasta
```

Temporary and failed-read outputs are retained under `collapse/tmp/` for
troubleshooting.

!!! important
    For demultiplexed bulk runs, provide `--sample` so that downstream
    metadata can be associated with the correct sample.
