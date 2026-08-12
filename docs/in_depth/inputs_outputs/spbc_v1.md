# Visium V1 spatial barcode whitelist

For spatial datasets, `longairr collapse` determines the molecular and spatial
identity of every read by annotating UMI and Spatial Barcode Sequences.

To omit introducing invalid spatial locations, which would break downstream
analysis due to missing coordinates, LongAIRR utilizes a whitelist approach, where
the spatial identity of every read gets validated against a list of known spatial barcode sequences.

For `Visium V1` datasets, LongAIRR can utilize the predefined spatial-barcode whitelist
that contains 4992 unique spatial barcode sequences and its coordinates. 
LongAIRR expects the Visium V1 coordinate whitelist:

```text
visium-v1_coordinates.txt
```

The file is supplied with 10x Genomics Space Ranger and is subject to the
applicable 10x Genomics terms.

Follow the
[10x Genomics guidance for locating spatial barcode files](https://kb.10xgenomics.com/s/article/360041426992-Where-can-I-find-the-Space-Ranger-barcode-inclusion-list-formerly-barcode-whitelist-and-their-coordinates-on-the-slide).


!!! info "See also"
    Check the documentation for `longairr collapse` information on how to correctly
    pass the **spatial barcode whitelists** using the right parameter when manually
    running LongAIRR

    Go to [LongAIRR collapse](../longairr_modules/collapse.md)
