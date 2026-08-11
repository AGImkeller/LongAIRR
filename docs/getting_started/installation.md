# Getting started

This guide takes you from downloading LongAIRR to choosing the workflow that
matches your library and starting data.

**Development versions** and source code are available on [GitHub](https://github.com/AGImkeller/LongAIRR)

Setting up **reference databases** is described further [below](#extra-dependencies)

## Installation | Linux

### Prerequisites

#### Install Conda / Mamba 

Install Miniforge (a Conda-based environment manager) using the following commands:

Follow the on-screen information during Miniforge's installation. More information can be found [**here**](https://github.com/conda-forge/miniforge/)
```markdown
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"

bash Miniforge3-$(uname)-$(uname -m).sh
conda activate base
```

### GitHub

```bash
git clone https://github.com/AGImkeller/LongAIRR.git
cd LongAIRR
```

The default branch contains the latest stable release. The `devel` branch
contains active development and may change without notice.


```bash
bash install.sh \
  --env TRUE \
  --scripts-dir ./longairr_scripts/
```

The script creates the `longairr` Conda environment and installs the LongAIRR
command below `$HOME/.local/bin/longairr/`.

Refresh the shell and verify the installation:

```bash
source "$HOME/.bashrc"
conda activate longairr
longairr --version
longairr --help
```

If you want to **deinstall LongAIRR after manual installation** from GitHub:
From the LongAIRR repository:

```bash
conda deactivate
bash deinstall.sh
```

## Requirements

### Extra dependencies

- **longairr basecall** requires a compatible GPU and Dorado installation. If you
  install LongAIRR manually from GitHub, Dorado will be installed on your system.
  
  If the reads have already been basecalled, the remaining LongAIRR modules can
  be run without a GPU and without a Dorado installation.

```bash
  # Install Dorado only
  bash install.sh \
    --env FALSE \
    --dorado TRUE
```

- **longairr collapse** requires spatial barcode whitelist from **10x SpaceRanger**
  for spAIRR datasets (Visium / Visium HD 3').
  Refer to our [Spatial Barcode Whitelist](../index.md#in-depth) section

- **longairr airr** requires **IgBLAST databases and IMGT germline references**. They
  can be downloaded using the installation script:

```bash
  # Download and set up the database references (no env, no dorado)
  bash install.sh \
    --fetch-db TRUE \
    --save-db /path/to/reference-parent/ \
    --species human \
    --env FALSE \
    --dorado FALSE \ 
    --scripts-dir ./longairr_scripts/
```

  set `--env TRUE` if you also want to install the conda environment. (Not necessary
  if installed with Bioconda)

  Available species are:

```text
  human, mouse, rat, rabbit, rhesus_monkey
```

  For a human installation, the resulting structure is:

```text
  /path/to/reference-parent/
  └── databases/
      ├── igblast/
      └── germlines/
          └── imgt/
              └── human/
                  └── vdj/
```

  The example Snakemake configurations use the parent `databases/` directory.

___

## Choose your starting point

| Starting data or library | Recommended starting point |
| --- | --- |
| ONT **POD5 files** | Basecall on a GPU, then continue from FASTQ |
| ONT or PacBio HiFi **FASTQ** | Start with `longairr filter` |
| **Visium V1** spatial AIRR | Use the spatial workflow with a Visium V1 coordinate whitelist |
| **Visium HD 3′** spatial AIRR | Use the spatial workflow with a LongAIRR_whitelist SQLite index |
| Multiplexed **Takara SMART-Seq BCR** | Use the bulk workflow with UDI demultiplexing |
| Filtered FASTA or intermediate LongAIRR output | Continue manually from the relevant module |

Basecalling is kept outside the supplied Snakemake workflows because it has
different hardware requirements and is often run on a dedicated GPU system.

!!! important
    - Refer to the [Example LongAIRR Workflows chapters](../index.md#example-longairr-workflows) for
    a detailed description depending on your input dataset.
    - To understand additional inputs like **barcode anchor files** and **spatial barcode whitelists**, refer to the [in-depth](../index.md#in-depth) chapters
