# Output directories and files

LongAIRR keeps major module outputs as restart points and saves temporary
files within module-specific `tmp/` directories.

## Spatial run directories

The current spatial Snakemake workflow produces a structure similar to:

```text
longairr_results/
├── .longairr/
│   ├── run.json
│   └── metadata/
├── filter_qc/
│   ├── longairr_filtered.fastq
│   ├── longairr_filtered.fasta
│   └── qc_report/
├── collapse/
│   ├── 4_longairr_consensus.fasta
│   └── tmp/
├── seqtag/
│   ├── Ig/
│   │   └── combined_Ig.fasta
│   ├── TCR/
│   │   └── combined_TCR.fasta
│   └── tmp/
├── airr/
│   ├── ig_p_parse-select.tsv
│   └── tr_p_parse-select.tsv
├── snakemake_logs/
├── config.yaml
├── summary.tsv
└── longairr_report.html
```

The exact locus-specific files depend on the configured `seqtag` split and
requested `airr` loci.

## Multiplexed bulk run directories

```text
longairr_results/
├── .longairr/
├── filter_qc/
├── sample_demux/
│   ├── <sample-1>/
│   │   ├── split_UDI-<sample-1>.fasta
│   │   ├── collapse/
│   │   ├── seqtag/
│   │   └── airr/
│   └── <sample-2>/
│       ├── split_UDI-<sample-2>.fasta
│       ├── collapse/
│       ├── seqtag/
│       └── airr/
├── snakemake_logs/
├── config.yaml
├── summary.tsv
└── longairr_report.html
```

## Main output files

Exemplary main results from a combined BCR / TCR dataset:

| Module | File | Interpretation |
| --- | --- | --- |
| `collapse` | `4_longairr_consensus.fasta` | Consensus sequence for each retained molecule group |
| `airr` | `ig_p_parse-select.tsv` | AIRR table - prod. immunoglobulin |
| `airr` | `ig_ph_parse-select.tsv` | AIRR table - prod. heavy-chain immunoglobulin |
| `airr` | `tr_p_parse-select.tsv` | AIRR table - prod. T-cell receptor |
| `report` | `summary.tsv` | Count summary table from module metadata |
| `report` | `longairr_report.html` | Interactive HTML report |
|  | `config.yaml` | Config file copied when using the snakemake workflow |

!!! info "See also"
    Find an exemplary [HTML report](../../vignettes/longairr_report.html) provided in the repository.

    Underlying file paths will break, since the report is disconnected from its
    corresponding results directory.


## Temporary output files

Temporary outputs are intentionally retained to support troubleshooting and
method validation. They should not normally be treated as the final result of
a sample.
