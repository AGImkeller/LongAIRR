
[![bioRxiv](https://img.shields.io/badge/bioRxiv-10.64898%2F2026.06.22.733709-B31B1B.svg)](https://doi.org/10.64898/2026.06.22.733709)
[![Install from GitHub](https://img.shields.io/badge/install-GitHub-2ea44f.svg)](./getting_started/installation.md#github)

# LongAIRR

![Overview of the LongAIRR workflow](images_design/images/longairr_profiling_overview.png)

**LongAIRR** is a modular command-line tool for processing and annotating
full-length immunoglobulin and T-cell receptor sequences from long-read
sequencing data.

LongAIRR can process AIRR reads generated with Oxford Nanopore Technologies and PacBio HiFi 
sequencing using the following bulk and spatial library protocols:

  * [10x Visium V1 - Spatial Gene Expression Vers.: CG000239 RevF](https://www.10xgenomics.com/support/spatial-gene-expression-fresh-frozen/documentation/steps/library-construction/visium-spatial-gene-expression-reagent-kits-user-guide)
  * [10x Visium HD 3' - Spatial Gene Expression Vers.: CG000805 RevB](https://www.10xgenomics.com/support/spatial-gene-expression-hd-three-prime/documentation/steps/library-construction/visium-hd-3-prime-spatial-gene-expression-user-guide)
  * [SMART-Seq Human BCR (with UMIs)](https://www.takarabio.com/products/next-generation-sequencing/immune-profiling/human-repertoire/smart-seq-human-bcr-with-umis?srsltid=AfmBOoqz0SB9vJtwLHpGINeMqu9hOhdTcYTiH2PtZP4P2h7OG2y7NGmy)

---

**Find an overview of chapters included in this documentation** [below](#getting-started)

Find the preprint on **bioRxiv**, doi: [2026.06.22.733709](https://doi.org/10.64898/2026.06.22.733709)

---

## What LongAIRR is designed for

- **Reproducible processing of spatial AIRR data:** Long-read spatial AIRR (spAIRR)
  sequencing currently lacks an established standard processing workflow.
  **LongAIRR** provides a modular workflow that streamlines 
  preprocessing, preserving spatial information and generating AIRR-compliant 
  outputs. This supports reproducible analyses and facilitates comparisons 
  across datasets and studies.

- **Reliable receptor reconstruction from long reads:** LongAIRR identifies
  UMIs and spatial barcodes, groups reads representing the same molecule and
  generates consensus sequences before V(D)J annotation. Our approach introduces
  an **adaptive filtering** strategy that dynamically refines read-selection and 
  significantly improves consensus accuracy, enabling high-confidence sequence
  reconstruction independent of platform-specific sequencing error profiles.

- **Bulk and spatial AIRR processing:** LongAIRR supports sample
  demultiplexing for bulk libraries and preserves spatial-barcode information
  for spatially resolved B- and T-cell receptor analysis.

---

## Getting started

| Section | Description |
| --- | --- |
| [Installation and setup](./getting_started/installation.md) | Install LongAIRR, reference setup, starting points |
| [Release Notes](./getting_started/changelog.md) | Changelog |

## In-depth

| Section | Description |
| --- | --- |
| [LongAIRR modules](./in_depth/longairr_modules/overview.md) | Functionalities, parameters |
| [Expected inputs / Spatial Barcode Whitelists](./in_depth/inputs_outputs/input_files.md) | Barcode-anchors, References, Whitelists |
| [Expected outputs / AIRR format](./in_depth/inputs_outputs/output_files.md) | Result-directories and files, Datafields in AIRR format |

## Example LongAIRR Workflows

| Section | Description |
| --- | --- |
| [Run LongAIRR manually](./example_workflows/manual.md) | Command-line usage examples |
| [Spatial Snakemake workflow](./example_workflows/snakemake_spatial.md) | Configure and run the spatial snakemake workflow |
| [Bulk Snakemake workflow](./example_workflows/snakemake_bulk.md) | Configure and run the bulk snakemake workflow |

## spAIRR downstream analysis

- [Vignette 1 - Chapter overview](./vignettes/vignette_1_spAIRR_start/vignette1_overview.md)
    - [Part 1 - Start spatial AIRR analysis with LongAIRR output](./vignettes/vignette_1_spAIRR_start/longairr_vignette1_part1.md)
    - [Part 2 - Explore spatial resolutions with AIRR + SpaceRanger](./vignettes/vignette_1_spAIRR_start/longairr_vignette1_part2.md)
    - [Part 3 - Interoperability with `scRepertoire`](./vignettes/vignette_1_spAIRR_start/longairr_vignette1_part3.md)

## About | Misc

- [Contact & Citation](./about_misc/contact_citation.md)
- [FAQ / Troubleshooting](./about_misc/troubleshooting.md)
- [Used Software](./about_misc/software_references.md)
- [License](./about_misc/license.md)
