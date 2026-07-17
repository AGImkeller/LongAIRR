# LongAIRR 1.2.0-devel

Introducing the 'longairr report' module, replacing the per-module-summary logic.

Now each module now writes run-specific metadata into '/.longairr/' and
'longairr report' extracts corresponding metadata for each module and
generates the legacy summary.tsv and longairr_report.html files.

Tested for Visium V1 and Visium HD 3' datasets, both while running LongAIRR via
the terminal and as part of a snakemake workflow.

New metadata approach does not exist for 'longairr basecall' and 'longairr demux'
yet and will be implemented and tested as part of the next version.

# LongAIRR 1.1.0-devel

Introducing functionality to use a spatial barcode whitelist for Visium HD 3' datasets
derived from SpaceRanger output metadata. 

This spatial barcode whitelist can be generated with our extension package
'Longairr_whitelist'.

The current version of using two input spatial barcode whitelists (SPBC1 / SPBC2) will be deprecated and removed in 
upcomming versions and possibly introduced again once official SPBC-whitelists for Visium HD 3' datasets are publicly provided by 10x Genomics.

# LongAIRR 1.0.0

First public LongAIRR version

# LongAIRR 0.99.7.6

LongAIRR goes public

