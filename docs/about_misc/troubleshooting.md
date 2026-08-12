#  FAQ | Troubleshooting

If you come across an error, feel free to submit a [GitHub-issue](https://github.com/AGImkeller/LongAIRR/issues) or [contact](../about_misc/contact_citation.md) us directly.

Below you can find short descriptions for frequent errors.

## `longairr` is not found

Activate the environment and refresh the shell:

```bash
source "$HOME/.bashrc"
conda activate longairr
longairr --version
```

## A Snakemake path cannot be resolved

Use absolute paths in `config.yaml`. Avoid `~` and confirm that `OUTPUT` has the
intended trailing directory structure.

Run a dry-run:

```bash
snakemake --dry-run --printshellcmds \
  --snakefile /path/to/Snakefile \
  --configfile /path/to/config.yaml
```

## Visium V1 collapse rejects the input

Confirm that:

- `COLLAPSE_LIBRARY` is `visium`;
- `--visium-spbc` or `VISIUM_SPBCS_TXT` is provided;
- the coordinate whitelist exists and is readable;
- `SPBCUMI` is used where appropriate.

## Visium HD collapse rejects the input

Confirm that:

- `COLLAPSE_LIBRARY` is `visiumhd`;
- a valid `--hd-spbc-index`/`VISIUMHD_SPBC_INDEX` is provided;
- the grouping field is `UMISPBCID`;
- the index was built from the matching spatial experiment.

## Few reads pass `seqtag`

- Check the anchor sequences.
- Check read orientation.
- Consider the reverse complement of the anchor.
- Confirm that the search window spans the expected sequence location.
- Review `seqtag` failed outputs in its temporary directory.

## `report` cannot find metadata

The supplied path must be the run root containing:

```text
.longairr/run.json
```

For demultiplexed bulk runs, ensure `--sample` was supplied consistently to
the sample-level modules.

Validate without writing output:

```bash
longairr report --validate-only /path/to/run-root/
```

## Results were moved

Move the complete run directory, including `.longairr/`, and regenerate the
report. LongAIRR will preserve original paths and resolve relocated files where
possible.

## Getting help

Check the command-specific help:

```bash
longairr <command> --help
```

Report reproducible problems through the
[LongAIRR issue tracker](https://github.com/AGImkeller/LongAIRR/issues). Include
the LongAIRR version, command/configuration, relevant log, and operating
environment.
