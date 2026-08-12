
[![GitHub release](https://img.shields.io/github/v/release/AGImkeller/LongAIRR)](https://github.com/AGImkeller/LongAIRR/releases)
[![Documentation Status](https://app.readthedocs.org/projects/longairr/badge/?version=latest)](https://longairr.readthedocs.io/en/latest/)
[![Install from GitHub](https://img.shields.io/badge/install-GitHub-2ea44f.svg)](./docs/getting_started/installation.md#github)


# LongAIRR <img src="./docs/images_design/images/longairr_logo_small.png" align="right" height="150" alt="logo" />

[![bioRxiv](https://img.shields.io/badge/bioRxiv-10.64898%2F2026.06.22.733709-B31B1B.svg)](https://doi.org/10.64898/2026.06.22.733709)


**LongAIRR** is a modular command-line framework for processing and annotating 
full-length adaptive immune receptor repertoire (AIRR) sequences from 
long-read bulk and spatial transcriptomic libraries.
LongAIRR supports Oxford Nanopore Technologies (ONT) and PacBio HiFi data and
combines read filtering, UMI and spatial-barcode annotation, adaptive 
read filtering, consensus generation, receptor tagging and V(D)J annotation
to produce AIRR-compliant outputs. It can be run manually or integrated into
workflow managers such as Snakemake. Its outputs are interoperable with 
established downstream AIRR analysis frameworks including [Immcantation](https://immcantation.readthedocs.io/en/stable/) and [scRepertoire](https://www.bioconductor.org/packages/release/bioc/vignettes/scRepertoire/inst/doc/vignette.html).

<p align="center">
  <img src="./docs/images_design/images/longairr_profiling_overview.png" width="800" />
</p>

Supported library protocols (see Fig. 1):

  * [10x Visium V1 - Spatial Gene Expression Vers.: CG000239 RevF](https://www.10xgenomics.com/support/spatial-gene-expression-fresh-frozen/documentation/steps/library-construction/visium-spatial-gene-expression-reagent-kits-user-guide)
  * [10x Visium HD 3' - Spatial Gene Expression Vers.: CG000805 RevB](https://www.10xgenomics.com/support/spatial-gene-expression-hd-three-prime/documentation/steps/library-construction/visium-hd-3-prime-spatial-gene-expression-user-guide)
  * [SMART-Seq Human BCR (with UMIs)](https://www.takarabio.com/products/next-generation-sequencing/immune-profiling/human-repertoire/smart-seq-human-bcr-with-umis?srsltid=AfmBOoqz0SB9vJtwLHpGINeMqu9hOhdTcYTiH2PtZP4P2h7OG2y7NGmy)

---

# Getting started

For installation instructions, example workflows, module documentation and 
downstream analysis please refer to the [**LongAIRR documentation**](https://longairr.readthedocs.io/en/latest/)


# Citation

If you use LongAIRR in your work, please cite:

> Schuck J, Ortega Iannazzo S, Mahmoud Z, Gwellem Anchang C, Hasse LM,
> Weber K, and Imkeller K. Consistent consensus-based annotation of spatial
> adaptive immune receptor repertoires from long-read sequencing using
> LongAIRR. Preprint at
> [bioRxiv](https://www.biorxiv.org/content/10.64898/2026.06.22.733709v1)
> (2026). DOI:
> [10.64898/2026.06.22.733709](https://doi.org/10.64898/2026.06.22.733709).

---

# Authors

[Jonas Schuck](https://github.com/Jonas-Schuck), [Katharina Imkeller](https://github.com/imkeller)

**Contact**: Schuck@med.uni-frankfurt.de

**Issues/Bug-report**: [LongAIRR-Issues](https://github.com/AGImkeller/LongAIRR/issues)

___
[**BACK TO TOP**](#longairr)
___