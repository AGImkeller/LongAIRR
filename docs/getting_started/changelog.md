# Changelog

All notable changes to this project will be documented in this file.
Changes and documentation are for the default branch, inheriting stable releases.

# LongAIRR 1.1.0

## Added

  - Support for spatial barcode whitelists for visium hd 3' datasets generated
    by our companion package **LongAIRR-Whitelist**. Supporting ONT datasets as of now.
  - `longairr report` module was added.
  - **ReadTheDocs** documentation

## Fixed

  - Bug fixed for bulk datasets, now omits headers and sequences for ultra-short
  sequences.

## Changed

  - New metadata processing in every longairr module replaces the summary sections.
    Metadata is written to ./.longairr for every module and processed by the new
    longairr report module to write structured summary.tsv and longairr_report.html
    reports

# LongAIRR 1.0.0

- Initial release
