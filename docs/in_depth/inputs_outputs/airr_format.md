# AIRR-formatted output

`longairr airr` annotates reconstructed receptor sequences and writes the
results as tab-separated AIRR Rearrangement tables. The AIRR format provides
standard field names for annotated immunoglobulin and T-cell receptor
sequences, which facilitates exchange between repertoire-analysis tools.

The complete AIRR Rearrangement specification is available from the
[AIRR Community](https://docs.airr-community.org/en/latest/datarep/rearrangements.html).

## What does one row represent in spAIRR datasets?

LongAIRR performs UMI- / sequence group-based consensus reconstruction before V(D)J annotation.
Consequently, one row normally represents one reconstructed consensus
sequence rather than one raw sequencing read.

The molecular unit represented by a row depends on the grouping field used by
`longairr collapse`:

| Library | Typical grouping unit |
| --- | --- |
| Bulk AIRR | UMI |
| Visium V1 | UMI and spatial barcode |
| Visium HD 3′ | UMI and corrected spatial barcode identifier |

## Output files

Depending on the selected locus and filtering options, `longairr airr` writes
tables such as:

```text
airr/
├── ig_p_parse-select.tsv
├── ig_ph_parse-select.tsv
└── tr_p_parse-select.tsv
```

The filename indicates the applied filtering:

| Identifier | Meaning |
| --- | --- |
| `_p_` | Productive rearrangements |
| `_ph_` | Productive immunoglobulin heavy-chain rearrangements |

See the [`longairr airr` module](../longairr_modules/airr.md) for the complete command
and output description.

## Core AIRR fields

LongAIRR uses IgBLAST and Change-O to populate the AIRR Rearrangement table.
The table can contain many fields; the following groups cover those most
commonly used for initial downstream analysis.

| Information | Important fields | Description |
| --- | --- | --- |
| Sequence | `sequence_id`, `sequence`, `rev_comp` | Consensus-sequence identifier, nucleotide sequence and orientation |
| Rearrangement status | `productive`, `vj_in_frame`, `stop_codon` | Indicators describing whether the rearrangement is predicted to encode a functional receptor chain |
| Gene assignment | `locus`, `v_call`, `d_call`, `j_call`, `c_call` | Assigned receptor locus and V, D, J and constant-region genes |
| Junction | `junction`, `junction_aa`, `junction_length` | Rearranged junction sequence, translation and length |
| Alignment | `sequence_alignment`, `germline_alignment`, `v_cigar`, `d_cigar`, `j_cigar` | Query-to-germline alignment information |
| Coordinates | `v_sequence_start`, `v_sequence_end`, `d_sequence_start`, `j_sequence_start`, and related fields | Positions of assigned gene segments in the reconstructed sequence |
| Consensus support | `consensus_count` | Number of reads used to construct the consensus sequence |

Empty values are valid in AIRR tables. For example, `d_call` is generally
empty for receptor chains that do not contain a D segment, and individual
alignment fields may remain empty when an assignment is unavailable.

## LongAIRR processing metadata

In addition to standard AIRR fields, LongAIRR carries molecular and spatial
metadata from consensus reconstruction into the final table. The available
columns depend on the library type and selected LongAIRR options.

### Consensus and molecule fields

| Field | Description |
| --- | --- |
| `group` | Identifier used to group reads for consensus construction. This is typically a UMI for bulk data and a combined UMI–spatial-barcode identifier for spatial data. |
| `umi` | Annotated unique molecular identifier. |
| `n_orig` | Number of reads in the molecular group before group-specific filtering. |
| `n_keep` | Number of reads retained adaptive group filtering, before optional subsampling. |
| `consensus_count` | Number of retained reads that were used for consensus construction after optional subsampling. This is an AIRR-standard field populated by LongAIRR. |

The three count fields describe successive stages of consensus generation:
`n_orig` records the grouped reads, `n_keep` the filtered reads, and
`consensus_count` the reads ultimately aligned for consensus generation. They
should not be interpreted interchangeably.

### Spatial fields

| Field | Library | Description |
| --- | --- | --- |
| `spbc` | Visium V1 and Visium HD 3′ | Annotated spatial-barcode sequence. For the Visium HD index-based workflow, this retains the *observed* raw barcode sequence. |
| `spbcid` | Visium HD 3′ | Corrected Visium HD spatial identifier, e.g., 2 µm square identifier annotated by SpaceRanger. |
| `x`, `y` | Spatial libraries | Spatial coordinates associated with the annotated barcode. |
| `umispbc` | Visium HD 3′ | Combined UMI and observed raw spatial-barcode sequence retained for traceability. |
| `prcount` | Spatial libraries | Number of reads supporting the retained spatial-barcode annotation during consensus construction. Useful only if the UMI is used as a group identifier for spatial datasets. |

Bulk output does not contain spatial fields. Some intermediate FASTA headers
contain additional processing information that is not necessarily retained as
a column in every final AIRR table.

## Read a LongAIRR AIRR table in R

```r
library(dplyr)
library(readr)

airr <- read_tsv(
  "longairr_results/airr/ig_ph_parse-select.tsv",
  show_col_types = FALSE
)

airr %>%
  select(sequence_id, locus, productive,
         v_call, d_call, j_call, c_call,
         group, consensus_count,
         any_of(c("spbcid", "umi", "spbc", "x", "y"))) %>%
  head()
```

Use `any_of()` for library-dependent columns so that the same inspection code
also works with bulk AIRR output.

## Read the table in Python

```python
import pandas as pd

airr = pd.read_csv(
    "longairr_results/airr/ig_ph_parse-select.tsv",
    sep="\t"
)

print(airr.head())
```

LongAIRR-specific columns remain available when the table is imported into
downstream frameworks, although individual packages may use only the standard
AIRR fields they recognize.
 
