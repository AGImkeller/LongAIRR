#!/usr/bin/env bash

#================================================================#
#
#        Script:  imgt2igblast.sh
#         Usage:  Internal script used by the install.sh script
#
#   DESCRIPTION:  Convert IMGT germline sequences to IgBLAST database
#
#        AUTHOR:  Jonas Schuck, jschuckdev@gmail.com
#    BUG-REPORT:  https://github.com/AGImkeller/LongAIRR/issues
#
#          NOTE: Script taken and extended from:
#                https://bitbucket.org/kleinstein/immcantation/src/master/scripts/imgt2igblast.sh
#
# Credits to creators:
#        Author:  Jason Anthony Vander Heiden
#          Date:  2016.11.21
#        Source:  (see NOTE)
#
#================================================================#

# Default argument values
OUTDIR="."
SPECIES_LIST=("human" "mouse" "rhesus_monkey")  # Default species list

# Show general help message
show_help () {
    echo -e "Usage: $(basename $0) [OPTIONS]"
    echo -e "  -i  Input directory containing germlines in the form:"
    echo -e "      <species>/vdj/imgt_<species>_<chain><segment>.fasta."
    echo -e "  -o  Output directory for the built database."
    echo -e "  --species  Comma-separated list of species to include. Defaults to all species."
    echo -e "  -h  This message."
}

# Get command-line arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -i)
            GERMDIR=$(realpath "$2")
            GERMDIR_SET=true
            shift 2
            ;;
        -o)
            OUTDIR="$2"
            OUTDIR_SET=true
            shift 2
            ;;
        --species)
                if [ -n "$2" ]; then
                    IFS=',' read -ra SPECIES_LIST <<< "$2"
                    shift 2
                else
                    echo "--species option requires an argument." >&2
                    exit 1
                fi
                ;;
        -h)
            help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Exit if no germline directory provided
if [[ ! $GERMDIR_SET ]]; then
    echo "You must specify an input directory using the -i option" >&2
    exit 1
fi

# Create and set directories
OUTDIR=$(realpath "${OUTDIR}")
mkdir -p "${OUTDIR}/fasta"
TMPDIR=$(mktemp -d)

# Create fasta files of each species, chain, and segment combination
for SPECIES in "${SPECIES_LIST[@]}"; do
    for CHAIN in IG TR; do
        # VDJ nucleotides
        for SEGMENT in V D J; do
            F=$(echo imgt_${SPECIES}_${CHAIN}_${SEGMENT}.fasta | tr '[:upper:]' '[:lower:]')
            cat ${GERMDIR}/${SPECIES}/vdj/imgt_${SPECIES}_${CHAIN}*${SEGMENT}.fasta > "${TMPDIR}/${F}"
        done

        # C nucleotides
        F=$(echo imgt_${SPECIES}_${CHAIN}_c.fasta | tr '[:upper:]' '[:lower:]')
        cat ${GERMDIR}/${SPECIES}/constant/imgt_${SPECIES}_${CHAIN}*C.fasta > "${TMPDIR}/${F}"

        # V amino acids
        F=$(echo imgt_aa_${SPECIES}_${CHAIN}_v.fasta | tr '[:upper:]' '[:lower:]')
        cat ${GERMDIR}/${SPECIES}/vdj_aa/imgt_aa_${SPECIES}_${CHAIN}*V.fasta > "${TMPDIR}/${F}"
    done
done


SCRIPT_TMP="${OUTDIR%/igblast}"
SCRIPT_DIR="${SCRIPT_TMP}/scripts/"
#SCRIPT_DIR="$(pwd)/databases/scripts/"
echo $SCRIPT_DIR
# Parse each created fasta file to create igblast database
cd "${TMPDIR}"

# List nucleotide files
NT_FILES=$(ls *.fasta 2>/dev/null | grep -E "imgt_(${SPECIES_LIST[*]// /|}).+\.fasta")
for F in ${NT_FILES}; do
    python "${SCRIPT_DIR}/clean_imgtdb.py" "${F}" "${OUTDIR}/fasta/$(basename "${F}")"
    makeblastdb -parse_seqids -dbtype nucl -in "${OUTDIR}/fasta/$(basename "${F}")" \
        -out "${OUTDIR}/database/$(basename "${F}" .fasta)"
done

# List amino acid files
AA_FILES=$(ls *.fasta 2>/dev/null | grep -E "imgt_aa_(${SPECIES_LIST[*]// /|}).+\.fasta")
for F in ${AA_FILES}; do
    python "${SCRIPT_DIR}/clean_imgtdb.py" "${F}" "${OUTDIR}/fasta/$(basename "${F}")"
    makeblastdb -parse_seqids -dbtype prot -in "${OUTDIR}/fasta/$(basename "${F}")" \
        -out "${OUTDIR}/database/$(basename "${F}" .fasta)"
done

# Remove temporary fasta files
cd -; rm -rf "$TMPDIR"
