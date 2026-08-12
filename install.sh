#!/usr/bin/bash -i

source ./longairr_scripts/longairr_version.sh

#================================================================#
#
#        Script:  install.sh
#         Usage:  bash install.sh [OPTIONS] longairr_dir
#
#   DESCRIPTION:  Script that sets up LongAIRR conda environment, moves scripts
#                 to `$HOME/.local/bin/longairr/` to make them available on the whole system
#                 and optionally downloads igblast and imgt databases,
#                 which is required input for LongAIRR.
#
#        AUTHOR:  Jonas Schuck, jschuckdev@gmail.com
#    BUG-REPORT:  https://github.com/AGImkeller/LongAIRR/issues
#
#================================================================#


version=${LONGAIRR_VERSION}


#====================Helper and Input functions====================#

# parameters
longairr_dir="./longairr_scripts/"

fetch_db="FALSE"
db_dir="./"
input_species=("human") # Default input species

env_bin="TRUE"
dorado_bin="FALSE"
verbose="TRUE"

# Show general help message
show_help() {
    echo ""
    echo "Usage: bash install.sh [OPTIONS]"
    echo ""
    echo "Description: Script that sets up LongAIRR conda environment, move scripts"
    echo "             to '$HOME/.local/bin/longairr' to make them available on the whole system and optionally"
    echo "             downloads igblast and imgt databases, which is necessary input for the LongAIRR workflow"
    echo ""
    echo "Options:"
    echo "  --scripts-dir VAL1,VAL2,...| Specify directory of the longairr scripts (default: ./longairr_scripts/) works if you run the installation script from within the downloaded github repo directory, state the proper directory otherwise"
    echo "  --fetch-db    TRUE | FALSE | Specify if you want to download imgt and igblast databases, which are necessary in downstream analysis"
    echo "  --save-db        VALUE     | Specify the directory where to save the databases"
    echo "  --species    VAL1,VAL2,... | Comma-separated list of species to download. Valid species are:
                                         human, mouse, rat, rabbit, rhesus_monkey (default: human)"
    echo "  --env         TRUE | FALSE | Specify if you want to (re-)install the conda environment"
    echo "  --dorado      TRUE | FALSE | Specify if you want to install Dorado on your system"
    echo "  --verbose     TRUE | FALSE | Additional runtime information printed to the stdout (default: TRUE)"
    echo "  -h, --help                 | Show this help message and exit"
    echo "  -v, --version              | Show version information and exit"
    echo ""
    echo "Example:"
    echo "LONG (download required databases):"
    echo "     bash install.sh --fetch-db TRUE --save-db save/db/here/ --species human --env TRUE path/to/longairr/longairr_scripts/"
    echo ""
    echo "SHORT (set up conda env):"  
    echo "     bash install.sh"
    echo ""
}

# Show version information
show_version() {
    echo "LongAIRR version ${version}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scripts-dir)
      longairr_dir="$2"
      shift 2
      ;;
    --fetch-db)
      fetch_db=$(echo "$2" | tr '[:lower:]' '[:upper:]')
      if [[ "${fetch_db}" != "TRUE" && "${fetch_db}" != "FALSE" ]]; then
        echo "Error: Invalid value for --fetch-db. Must be TRUE or FALSE."
        show_help
        exit 1
      fi
      shift 2
      ;;
    --save-db)
      db_dir="$2"
      shift 2
      ;;
    --species)
      if [[ -n "$2" ]]; then
        input_species="$2"
        shift 2
      else
        echo "--species option requires an argument." >&2
        exit 1
      fi
      ;;
    --env)
      env_bin=$(echo "$2" | tr '[:lower:]' '[:upper:]')
      if [[ "${env_bin}" != "TRUE" && "${env_bin}" != "FALSE" ]]; then
        echo "Error: Invalid value for --env. Must be TRUE or FALSE."
        show_help
        exit 1
      fi
      shift 2
      ;;
    --dorado)
      dorado_bin=$(echo "$2" | tr '[:lower:]' '[:upper:]')
      if [[ "${dorado_bin}" != "TRUE" && "${dorado_bin}" != "FALSE" ]]; then
        echo "Error: Invalid value for --dorado. Must be TRUE or FALSE."
        show_help
        exit 1
      fi
      shift 2
      ;;
    --verbose)
      verbose=$(echo "$2" | tr '[:lower:]' '[:upper:]')
      if [[ "${verbose}" != "TRUE" && "${verbose}" != "FALSE" ]]; then
        echo "Error: Invalid value for --verbose. Must be TRUE or FALSE."
        show_help
        exit 1
      fi
      shift 2
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    -v|--version)
      show_version
      exit 0
      ;;
    *)
      echo "Error: Unexpected argument '$1'."
      show_help
      exit 1
      ;;
  esac
done

#======================Download igblast and imgt references=====================#
# NOTE: Installation logic taken from Immcantation documentation: https://changeo.readthedocs.io/en/stable/examples/igblast.html

# Fetch scripts from Kleinstein lab to download igblast and imgt databases
# Other two scripts (imgt2igblast.sh and fetch_imgtdb.sh) were updated with extended functionality and
# are saved locally in the repo


if [[ "${fetch_db}" == "TRUE" ]]; then
  # Define the base URL of the repository
  base_url="https://bitbucket.org/kleinstein/immcantation/raw/master/scripts"

  # Set up directories
  bin_dir=$HOME/.local/bin/
  db_subdir="${db_dir}databases/"

  igblast_dir="${db_subdir}igblast"
  imgt_dir="${db_subdir}germlines/imgt"
  target_dir="${db_subdir}scripts/"

  longairr_dbscripts="${longairr_dir}/db_scripts/"

  imgtdb_script="${longairr_dbscripts}fetch_imgtdb.sh"
  imgt2igblast_script="${longairr_dbscripts}imgt2igblast.sh"
  fetchigblastdb_script="${longairr_dbscripts}fetch_igblastdb.sh"
  cleanimgtdb_script="${longairr_dbscripts}clean_imgtdb.py"

  mkdir -p "${bin_dir}" "${igblast_dir}" "${imgt_dir}" "${target_dir}"

  cp "${imgtdb_script}" "${target_dir}"
  cp "${imgt2igblast_script}" "${target_dir}"

  # List of scripts to download
  scripts=(
    "fetch_igblastdb.sh"
    "clean_imgtdb.py"
  )

  for script in "${scripts[@]}"; do
    url="${base_url}/${script}"
    # Download the script and save it in the target directory
    curl -o "${longairr_dbscripts}/${script}" "${url}" || { echo "Failed to download \"${script}\""; exit 1; }
  done

  if [[ "${verbose}" == "TRUE" ]]; then
    echo "Finished downloading scripts. Saved to \"${longairr_dbscripts}\""
  fi

  cp "${imgtdb_script}" "${target_dir}"
  cp "${imgt2igblast_script}" "${target_dir}"
  cp "${fetchigblastdb_script}" "${target_dir}"
  cp "${cleanimgtdb_script}" "${target_dir}"

  chmod +x "${longairr_dbscripts}"/*
  chmod +x "${target_dir}"/*

  echo "Scripts copied to ${target_dir}"

  # Set up URL for the latest version of IgBLAST for Linux
  latest_url="https://ftp.ncbi.nih.gov/blast/executables/igblast/release/LATEST/"
  linux_tarball=$(curl -s "${latest_url}" | grep -oP 'ncbi-igblast-\d+\.\d+\.\d+-x64-linux\.tar\.gz' | head -n 1)

  if [[ -z "${linux_tarball}" ]]; then
    echo "Error: Could not find the latest Linux tarball for IgBLAST. Check download."
    exit 1
  fi

  # Following steps taken from: https://changeo.readthedocs.io/en/stable/examples/igblast.html
  # Download and extract the tarball for IgBLAST
  wget "${latest_url}${linux_tarball}" || { echo "Failed to download ${linux_tarball}"; exit 1; }
  tar -zxf "${linux_tarball}" -C "${db_subdir}" || { echo "Failed to extract ${linux_tarball}"; exit 1; }

  # Setup IgBLAST binaries and databases
  version=$(echo "${linux_tarball}" | grep -oP '\d+\.\d+\.\d+')
  igblast_version_dir="${db_subdir}ncbi-igblast-${version}"

  # Copy binaries to bin directory
  cp "${igblast_version_dir}/bin/"* "${bin_dir}"

  # Download reference databases and setup IGDATA directory
  "${target_dir}/fetch_igblastdb.sh" -o "${igblast_dir}"
  cp -r "${igblast_version_dir}/internal_data" "${igblast_dir}"
  cp -r "${igblast_version_dir}/optional_file" "${igblast_dir}"

  # Build IgBLAST database from IMGT reference sequences
  "${target_dir}/fetch_imgtdb.sh" -o "${imgt_dir}" --species "${input_species}"
  "${target_dir}/imgt2igblast.sh" -i "${imgt_dir}" -o "${igblast_dir}" --species "${input_species}"

  # Cleanup downloaded files
  rm -rf "${linux_tarball}" "${igblast_version_dir}"*
  rm "${fetchigblastdb_script}"
  rm "${cleanimgtdb_script}"

  if [[ "${verbose}" == "TRUE" ]]; then
    echo "Finished downloading databases. Saved to ${target_dir}"
  fi
fi

#===============================Install Dorado#================================#


if [[ "${dorado_bin}" == "TRUE" ]]; then

  # Download and install Dorado
  bin_dir=$HOME/.local/bin/longairr/  # Directory to add to PATH
  dorado_version="0.9.1"
  dorado_install_dir="${bin_dir}dorado-${dorado_version}-linux-x64"
  dorado_url="https://cdn.oxfordnanoportal.com/software/analysis/dorado-${dorado_version}-linux-x64.tar.gz"
  dorado_tmp_dir=$(mktemp -d)

  mkdir -p "${bin_dir}"

  echo "Downloading Dorado..."
  wget -q -O "${dorado_tmp_dir}/dorado.tar.gz" "${dorado_url}" || {
      echo "Failed to download Dorado."
      rm -rf "${dorado_tmp_dir}"
      exit 1
  }

  echo "Extracting Dorado..."
  tar -xzf "${dorado_tmp_dir}/dorado.tar.gz" -C "${dorado_tmp_dir}" || {
      echo "Failed to extract Dorado."
      rm -rf "${dorado_tmp_dir}"
      exit 1
  }

  echo "Installing Dorado into ${bin_dir}..."

  # Replace an existing installation of the same pinned Dorado version
  rm -rf "${dorado_install_dir}"

  mv "${dorado_tmp_dir}/dorado-${dorado_version}-linux-x64/" "${bin_dir}/dorado-${dorado_version}-linux-x64/"
  chmod +x "${bin_dir}/dorado-${dorado_version}-linux-x64/"

  # Cleanup
  rm -rf "${dorado_tmp_dir}"
  echo "Dorado installed successfully in ${bin_dir}"

  sed -i '/# >>> LongAIRR DORADO PATH >>>/,/# <<< LongAIRR DORADO PATH <<</d' "$HOME/.bashrc"

  cat >> "$HOME/.bashrc" <<EOF

# >>> LongAIRR DORADO PATH >>>
export PATH="\$PATH:${bin_dir}dorado-${dorado_version}-linux-x64/bin/"
# <<< LongAIRR DORADO PATH <<<
EOF

  echo "Dorado paths added to ~/.bashrc"
fi

#==============================Create conda env================================#

env_exists() {
  local env_name="$1"
  conda env list | awk '{print $1}' | grep -qx "${env_name}"
}

get_env_path() {
  local env_name="$1"
  conda env list | awk -v env="${env_name}" '$1 == env {print $NF; exit}'
}

if [[ "${env_bin}" == "TRUE" ]]; then

  # Define the environment name and necessary paths
  env_name="longairr"
  bin_dir=$HOME/.local/bin/longairr/  # Directory to add to PATH
  main_script="longairr.sh"           # Name of the main tool script, to create a symlink for

  # Check if Conda is installed
  if ! command -v conda &>/dev/null; then
    echo "Conda is not installed. Please install Conda first."
    exit 1
  fi

  # Create the Conda environment if it does not exist yet
  if ! env_exists "^${env_name}"; then
    mamba env create -f "$(dirname "$0")/environment.yml" || { echo "Failed to create conda environment"; exit 1; }
  else
    echo "Conda environment \"${env_name}\" already exists."
  fi

  mkdir -p "${bin_dir}"

  #conda_env_path=$(conda env list | grep "^${env_name} " | awk '{print $2}')
  conda_env_path="$(get_env_path "${env_name}")"
  env_bin="${conda_env_path}/bin/"

  # Ensure Conda environment exists
  if [ -z "$conda_env_path" ]; then
    echo "Conda environment '${env_name}' not found!"
    exit 1
  fi

  # Add LongAIRR section in .bashrc
  sed -i '/# >>> LongAIRR PATH >>>/,/# <<< LongAIRR PATH <<</d' "$HOME/.bashrc"

  # Add fresh block
  cat >> "$HOME/.bashrc" <<EOF

# >>> LongAIRR PATH >>>
export PATH="\$PATH:${bin_dir}"
# <<< LongAIRR PATH <<<
EOF

  echo "LongAIRR paths added to ~/.bashrc"

  # Copy scripts to the target directory, avoiding overwrites
  for script in "${longairr_dir}"/*; do
    if [[ -f "${script}" ]]; then
      script_name=$(basename "${script}")

      # Check if the script already exists in the target directory
      if [[ -e "$bin_dir/$script_name" ]]; then
        continue
      fi
      cp "${script}" "${bin_dir}/${script_name}"
      chmod +x "${bin_dir}/${script_name}"
    fi
  done

  # Create symbolic link for the main script
  if [[ -f "${bin_dir}/${main_script}" ]]; then
    ln -sf "${bin_dir}/${main_script}" "${bin_dir}/longairr"
  fi

  # Install the LongAIRR logo used by the self-contained HTML report.
  local_logo="$(dirname "$0")/docs/images_design/images/longairr_logo_small.png"

  if [[ -f "${local_logo}" ]]; then
    cp -f "${local_logo}" "${bin_dir}/longairr_logo_small.png"
  else
    echo "WARNING: LongAIRR logo was not found at ${local_logo}. Reports will be generated without the logo."
  fi

  if [[ "${verbose}" == "TRUE" ]]; then
    echo ""
    echo "========================================================================"
    echo "|                                                                      |"
    echo "|----------------------LongAIRR Setup complete-------------------------|"
    echo "|                                                                      |"
    echo "|      Run 'source $HOME/.bashrc' to update your PATH                  |"
    echo "|                       or restart the terminal                        |"
    echo "|Then you can run the tool within the activated 'longairr' environment |"
    echo "|                                                                      |"
    echo "========================================================================"
    echo ""
  fi
fi
