# Run LongAIRR manually

Every LongAIRR module can be called independently. This is useful for testing,
restarting from an intermediate file, or integrating LongAIRR into another
workflow.

Jump to:
[spatial workflow](#spatial-workflow) ·
[multiplexed bulk workflow](#multiplexed-bulk-workflow) ·

!!! info "See also"
    The examples below show how outputs are chained with minimal information.
    Replace paths and parameter values with those appropriate for the experiment.

    Check the [LongAIRR modules](../in_depth/longairr_modules/overview.md),
    [Expected Inputs](../in_depth/inputs_outputs/input_files.md) and [Expected Outputs](../in_depth/inputs_outputs/output_files.md) for further details and
    descriptions of mandatory parameters, input files and which output files
    you can expect after each step.


## Spatial workflow

![spatial example workflow](../images_design/images/spatial_workflow_streamline.png)

### 1. Filter reads

```bash
longairr filter \
  --min-qual 17 \
  --minl 420 \
  --maxl 6000 \
  input.fastq \
  /path/to/results/
```

### 2. Annotate barcodes and build consensus sequences

**Visium V1**:

```bash
longairr collapse \
  --demux false \
  --library visium \
  --group-field SPBCUMI \
  --visium-spbc /path/to/visium-v1_coordinates.txt \
  /path/to/r1_anchor.fasta \
  /path/to/results/filter_qc/longairr_filtered.fasta \
  /path/to/results/
```

**Visium HD 3′**:

```bash
longairr collapse \
  --demux false \
  --library visiumhd \
  --group-field UMISPBCID \
  --hd-spbc-index /path/to/visium_whitelist.sqlite \
  /path/to/r1_anchor.fasta \
  /path/to/results/filter_qc/longairr_filtered.fasta \
  /path/to/results/
```

Add the experiment-specific adaptive-filtering, consensus, and performance
parameters after checking `longairr collapse --help`. 

### 3. Tag and split receptor loci

```bash
longairr seqtag \
  --split true \
  --split-regex Ig,TCR \
  --pf ISOTYPE \
  /path/to/constant_chain_anchors.fasta \
  /path/to/results/collapse/4_longairr_consensus.fasta \
  /path/to/results/
```

### 4. Run V(D)J annotation

```bash
longairr airr \
  --loci ig \
  /path/to/databases/igblast/ \
  /path/to/databases/germlines/imgt/human/vdj/ \
  /path/to/results/seqtag/Ig/combined_Ig.fasta \
  /path/to/results/

longairr airr \
  --loci tr \
  /path/to/databases/igblast/ \
  /path/to/databases/germlines/imgt/human/vdj/ \
  /path/to/results/seqtag/TCR/combined_TCR.fasta \
  /path/to/results/
```

### 5. Generate the report

```bash
longairr report /path/to/results/
```

---

## Multiplexed bulk workflow

![bulk example workflow](../images_design/images/bulk_workflow_streamline.png)

In this sequencing run multiple samples are demultiplexed after initial filtering.
Subsequent steps are shown for one of the two samples, e.g. `UID6`. Steps 2-4
should be repeated for all samples contained in a multiplexed run by exchanging
`--sample` and **input / output paths** respectively. **See notes below**

### 1. Filter and demultiplex

```bash
longairr filter input.fastq /path/to/results/

longairr demux \
  /path/to/UDI_barcodes.fasta \
  /path/to/results/filter_qc/longairr_filtered.fasta \
  /path/to/results/
```

### 2. Build sample-level consensus sequences

```bash
longairr collapse \
  --demux true \
  --library bulk \
  --sample UID6 \
  --group-field UMI \
  /path/to/UMI_anchor.fasta \
  /path/to/results/sample_demux/UID6/split_UDI-UID6.fasta \
  /path/to/results/sample_demux/UID6/
```

### 3. Optionally tag constant regions

```bash
longairr seqtag \
  --sample UID6 \
  --split false \
  --pf CONSTANT \
  /path/to/constant_igh_anchors.fasta \
  /path/to/results/sample_demux/UID6/collapse/4_longairr_consensus.fasta \
  /path/to/results/sample_demux/UID6/
```

### 4. Annotate AIRR sequences

```bash
longairr airr \
  --sample UID6 \
  --loci ig \
  /path/to/databases/igblast/ \
  /path/to/databases/germlines/imgt/human/vdj/ \
  /path/to/results/sample_demux/UID6/seqtag/longairr_seqtag_primers-pass.fasta \
  /path/to/results/sample_demux/UID6/
```

**`Repeat the sample-level steps for all demultiplexed samples and then run:`**

```bash
longairr report /path/to/results/
```

!!! important
    In demultiplexed bulk mode, supply the same `--sample` identifier to
    `collapse`, `seqtag`, and `airr` for its respective sample.
    This allows the report to connect
    sample-level metadata correctly.

## Example data

See the [synthetic Visium V1 demo dataset](https://github.com/AGImkeller/LongAIRR/tree/main/longairr_example_workflow/example_inputs) provided
in the repository as possible test input and the additional files needed to run it.
