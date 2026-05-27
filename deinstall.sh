#!/bin/bash

source ./longairr_scripts/longairr_version.sh

#================================================================#
#
#        Script:  deinstall.sh
#         Usage:  bash deinstall.sh
#
#   DESCRIPTION:  Script that uninstalls LongAIRR - removes the
#                 associated conda environment, PATH variables and
#                 installed software
#
#        AUTHOR:  Jonas Schuck, jschuckdev@gmail.com
#    BUG-REPORT:  https://github.com/AGImkeller/LongAIRR/issues
#
#================================================================#

VERSION=$LONGAIRR_VERSION

#====================Helper and Input functions====================#


# Show general help message
show_help() {
    echo ""
    echo "Usage: bash deinstall.sh [OPTIONS]"
    echo ""
    echo "Description: "
    echo "Uninstalls LongAIRR - removes the associated conda environment, PATH variables and cleans up the installation files."
    echo ""
    echo "Options:"
    echo "  -h, --help     | Show this help message and exit"
    echo "  -v, --version  | Show version information and exit"
    echo ""
}

# Show version information
show_version() {
    echo "LongAIRR version ${VERSION}"
}

# Define the environment name and target directory (where longairr scripts are installed)
ENV_NAME="longairr"
BIN_DIR=$HOME/.local/bin/longairr/  # Target bin directory
DORADO_BIN_DIR=${BIN_DIR}dorado-0.9.1-linux-x64/bin/

#==================== Remove Conda Environment =====================#

# Check if conda environment exists
if conda env list | grep -q "^$ENV_NAME"; then
    echo "Removing Conda environment: $ENV_NAME"
    conda env remove --name "${ENV_NAME}" || { echo "Failed to remove Conda environment"; exit 1; }
    echo "Conda environment '$ENV_NAME' removed."
else
    echo "Conda environment '$ENV_NAME' does not exist."
fi

#==================== Remove Scripts ====================#

# Delete the scripts installed in $BIN_DIR
echo "Removing installed scripts from $BIN_DIR..."
rm -r "$BIN_DIR"

#==================== Clean up Environment Variables =====================#

# Remove LongAIRR section from .bashrc
if grep -q "# >>> LongAIRR PATH >>>" "$HOME/.bashrc"; then
    echo "Removing LongAIRR PATH block from ~/.bashrc..."
    sed -i '/# >>> LongAIRR PATH >>>/,/# <<< LongAIRR PATH <<</d' "$HOME/.bashrc"
    echo "Removed. Run: source ~/.bashrc"
else
    echo "LongAIRR PATH block not found in ~/.bashrc."
fi
