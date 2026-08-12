# Vignette 1 - Spatial AIRR downstream exploration

This three-part vignette provides a practical starting point for downstream
analysis of spatial AIRR data generated with LongAIRR.

!!! info "Important"

    [**Part 2**](./longairr_vignette1_part2.md) and [**Part 3**](./longairr_vignette1_part3.md) continue from the 
    SCOPer-annotated `igh_clones` object generated in Part 1. Part 2 additionally requires
    matching SpaceRanger output, whereas Part 3 can be followed independently after
    completing Part 1.

---

**Code and corresponding sections are distributed across 3 separate files:**

### [**Part 1**](./longairr_vignette1_part1.md) - Start spatial AIRR analysis with LongAIRR output

Part 1 requires only a LongAIRR AIRR rearrangement table. It demonstrates how to:

  - Load and inspect LongAIRR AIRR output,
  - summarize the receptor repertoire overview,
  - assign IGH clones using SCOPer, 
  - visualize spatial distribution of exemplary clones

Visit this chapter: [**Open Part 1**](./longairr_vignette1_part1.md).

---

### [**Part 2**](./longairr_vignette1_part2.md) - Explore spatial resolutions with AIRR + SpaceRanger

Part 2 combines the annotated AIRR table with matching SpaceRanger output generated
during a LongAIRR-Whitelist workflow. It demonstrates how to:

  - integrate the tissue image as a background image
  - map native 2 µm spatial barcodes to 16 µm bins and segmented cell annotations
  - compare clone distributions across spatial resolutions

Visit this chapter: [**Open Part 2**](./longairr_vignette1_part2.md).

---

### [**Part 3**](./longairr_vignette1_part3.md) - Interoperability with `scRepertoire`


Part 3 imports the annotated AIRR table into `scRepertoire` and provides initial
examples of repertoire exploration. It demonstrates interoperability between
LongAIRR output and an established downstream AIRR analysis framework.

Visit this chapter: [**Open Part 3**](./longairr_vignette1_part3.md).

---

### Additional resources

- [LongAIRR GitHub repository](https://github.com/AGImkeller/LongAIRR)  
  Source code, installation instructions, example workflows and issue
  tracker.

- [LongAIRR-Whitelist GitHub
  repository](https://github.com/AGImkeller/LongAIRR_whitelist)  
  Companion workflow for generating sample-specific Visium HD 3′
  spatial-barcode indices.  
  *This link will become available once the repository is public.*

- [AIRR Community Data
  Standards](https://docs.airr-community.org/en/latest/datarep/overview.html)  
  Standards for representing and exchanging adaptive immune receptor
  repertoire data.

- [AIRR Rearrangement
  schema](https://docs.airr-community.org/en/latest/datarep/rearrangements.html)  
  Definitions of the standardized fields used in AIRR rearrangement
  tables.

- [Immcantation
  documentation](https://immcantation.readthedocs.io/en/stable/)  
  Framework for AIRR-seq processing and downstream repertoire analysis.

- [SCOPer documentation](https://scoper.readthedocs.io/)  
  Methods for assigning B-cell clonal relationships from AIRR-formatted
  data.

- [scRepertoire on
  Bioconductor](https://bioconductor.org/packages/scRepertoire/)  
  Installation, reference manual and vignettes for single-cell
  immune-receptor analysis.

- [scRepertoire GitHub
  repository](https://github.com/BorchLab/scRepertoire)  
  Source code, examples and issue tracker.