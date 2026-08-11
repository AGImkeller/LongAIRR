# Software references

LongAIRR combines established tools for long-read processing, AIRR annotation
and reproducible workflow execution. Exact environment specifications are
available in
[`environment.yml`](https://github.com/AGImkeller/LongAIRR/blob/devel/environment.yml).
and listed in the [installation chapter](../getting_started/installation.md).

## Software versions

| Software | Version in the LongAIRR environment | Role |
| --- | --- | --- |
| NanoPlot | 1.44.1 | Read quality-control reports |
| Samtools | 1.21 | BAM processing and sequence extraction |
| SeqKit | 2.9.0 | FASTA/FASTQ filtering, conversion and statistics |
| pRESTO | 0.7.5 | Anchor matching, grouping, alignment and consensus |
| Change-O | 1.3.3 | AIRR database creation and filtering |
| IgBLAST | 1.22.0 | V(D)J gene assignment |
| MUSCLE | 3.8.1551 | Multiple-sequence alignment through pRESTO |
| Snakemake | 7.32.4 | Example workflow execution |

Dorado is [installed separately](../getting_started/installation.md) when ONT basecalling is required.

## Publications and resources

- **Dorado:** Oxford Nanopore Technologies,
  [Dorado repository](https://github.com/nanoporetech/dorado).

- **NanoPlot:** De Coster, W., & Rademakers, R. (2023). NanoPack2: population-scale evaluation of long-read sequencing data. Bioinformatics, 39(5). [doi:10.1093/bioinformatics/btad311](https://doi.org/10.1093/bioinformatics/btad311)

- **Samtools:** Danecek, P., Bonfield, J. K., Liddle, J., Marshall, J., Ohan, V., Pollard, M. O., Whitwham, A., Keane, T., McCarthy, S. A., Davies, R. M., & Li, H. (2021). Twelve years of SAMtools and BCFtools. GigaScience, 10(2). [doi:10.1093/gigascience/giab008](https://doi.org/10.1093/gigascience/giab008)

- **SeqKit:** 
    - Wei Shen*, Botond Sipos, and Liuyang Zhao. 2024. SeqKit2: A Swiss Army Knife for Sequence and Alignment Processing. iMeta e191. doi:10.1002/imt2.191. 

    - Wei Shen, Shuai Le, Yan Li\*, and Fuquan Hu\*. SeqKit: a cross-platform and ultrafast toolkit for FASTA/Q file manipulation. PLOS ONE. doi:10.1371/journal.pone.0163962. 

- **pRESTO:** Vander Heiden, J.A., Yaari, G., Uduman, M., Stern, J. N., O’Connor, K. C., Hafler, D. A., Vigneault, F., & Kleinstein, S. H. (2014). pRESTO: a toolkit for processing high-throughput sequencing raw reads of lymphocyte receptor repertoires. Bioinformatics, 30(13), 1930–1932. [doi:10.1093/bioinformatics/btu138](https://doi.org/10.1093/bioinformatics/btu138)

- **Change-O:** Gupta, N. T., Vander Heiden, J.A., Uduman, M., Gadala-Maria, D., Yaari, G., & Kleinstein, S. H. (2015). Change-O: a toolkit for analyzing large-scale B cell immunoglobulin repertoire sequencing data. Bioinformatics, 31(20), 3356–3358. [doi:10.1093/bioinformatics/btv359](https://doi.org/10.1093/bioinformatics/btv359)

- **IgBLAST:** Ye, J., Ma, N., Madden, T. L., & Ostell, J. M. (2013). IgBLAST: an immunoglobulin variable domain sequence analysis tool. Nucleic Acids Research, 41(W1), W34–W40. [doi:10.1093/nar/gkt382](https://doi.org/10.1093/nar/gkt382)

- **Snakemake:** Köster, J., & Rahmann, S. (2012). Snakemake—a scalable bioinformatics workflow engine. Bioinformatics, 28(19), 2520–2522. [doi:10.1093/bioinformatics/bts480](https://doi.org/10.1093/bioinformatics/bts480)

- **Conda:** Anaconda Software Distribution. (2020). Anaconda Documentation. Anaconda Inc. Retrieved from https://docs.anaconda.com/


