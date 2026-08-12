# Required input files

LongAIRR combines user sequencing data with library-specific anchors and
reference databases.

| Command | Sequences Format | Extra input |
| --- | --- | --- |
| `basecall` | ONT POD5 files | // |
| `filter` | FASTQ | // |
| `demux` | FASTA | [UDI FASTA](#udi-anchor-fasta-bulk-only)|
| `collapse` | FASTA | [UMI/Barcode anchor FASTA](#umibarcode-anchor-fasta), [SPBC whitelist](#spatial-barcode-whitelists) | 
| `seqtag` | FASTA | [Constant-segment FASTA](#constant-segment-anchors) |
| `airr` | FASTA | [IgBLAST directory, germline directory](#airr-reference-databases) |
| `report` | /// | results-dir containing `.longairr/` metadata |


!!! info "See also"
    Check the documentation for each module about information on how to correctly
    pass sequence-input and extra-input files when manually running LongAIRR.

    Go to [LongAIRR modules](../longairr_modules/overview.md)

    Find example anchors provided in the package:

        longairr_example_workflow/example_inputs/required_anchors/
        ├── bulk_takara/
        └── spatial_visium/

## Extra input

### UDI anchor FASTA [Bulk only]

`longairr demux` expects one UDI per FASTA entry. Include only barcodes present in the current run.

```fasta
>UID12
GACGAGAG
>UID13
AGACTTGG
```

---

### UMI/Barcode anchor FASTA

`longairr collapse` uses the supplied anchor to locate and extract the UMI and,
where applicable, neighboring spatial-barcode sequence.

Example spatial R1 anchor:

```fasta
>r1
CTACACGACGCTCTTCCGATCT
```

The appropriate anchor and search window depend on the experimental library.

---

### Spatial Barcode Whitelists

Refer to the next section **Spatial Barcode Whitelists** on how to generate spatial barcode whitelists for 
[Visium V1](../inputs_outputs/spbc_v1.md) and [Visium HD 3'](../inputs_outputs/spbc_hd3.md) datasets using 10x Genomics SpaceRanger and our whitelist-builder
extension package **LongAIRR-Whitelist**.

---

### Constant-segment anchors

`longairr seqtag` accepts user-defined constant-region or other sequence
anchors. Their identifiers can encode receptor locus, isotype, or another
category used by `--split-regex`.

```fasta
>Ig | 1 | IGHA
GCATCCCCGACCAGC
>Ig | 2 | IGHA
AAGTCCGTGACATGC
>Ig | 3 | IGHG
CCACCAAGGGCCCAT
>Ig | 4 | IGHG
GGACTCTACTCCCTC
>Ig | 5 | IGHM
GGGAGTGCATCCGCC
...
>TCR | 16 | TRAC
ATTATTCCAGAAGAC
>TCR | 17 | TRBC
```

---

### AIRR reference databases

`longairr airr` requires:

```text
databases/
├── igblast/
└── germlines/
    └── imgt/
        └── <species>/
            └── vdj/
```

These can be prepared using `install.sh --fetch-db TRUE --env FALSE`. Refer to
the [Installation](../../getting_started/installation.md) instructions.
