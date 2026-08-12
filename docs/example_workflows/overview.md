# Workflow overview

LongAIRR is modular: every command can be run independently, while the provided
Snakemake workflows connect the commands into complete spatial and bulk
analyses.

Choose a workflow:

- [Run LongAIRR manually](manual.md)
- [Spatial Snakemake workflow](snakemake_spatial.md)
- [Bulk Snakemake workflow](snakemake_bulk.md)

## Complete spatial workflow

The spatial workflow expects a basecalled FASTQ file:

![spatial example workflow](../images_design//images/spatial_workflow_streamline.png)

The spatial workflow is provided as a complete
[Snakemake workflow](snakemake_spatial.md) and as a
[manual command chain](manual.md#spatial-workflow).

## Complete multiplexed bulk workflow

The bulk workflow inserts UDI-based demultiplexing before molecule-level
consensus generation:

![bulk example workflow](../images_design/images/bulk_workflow_streamline.png)

The multiplexed bulk workflow is provided as a complete
[Snakemake workflow](snakemake_bulk.md) and as a
[manual command chain](manual.md#multiplexed-bulk-workflow).

## Basecalling

Basecalling is kept outside the supplied Snakemake workflows because it has
different hardware requirements and may run on a dedicated GPU server. The
Snakemake workflows begin with the FASTQ produced by `longairr basecall` or
another compatible basecalling process.

## Module outputs as restart points

Important intermediate outputs are retained. In particular:

- `filter_qc/longairr_filtered.fasta`
- `sample_demux/<sample>/split_UDI-<sample>.fasta`
- `collapse/4_longairr_consensus.fasta`
- `seqtag/longairr_seqtag_primers-pass.fasta` or split locus FASTAs

These files can be used to restart a workflow manually or integrate LongAIRR
modules into another workflow manager.
