#!/usr/bin/env bash

#================================================================#
#
#        Script:  fetch_imgtdb.sh
#         Usage:  Internal script used by the install.sh script
#
#   DESCRIPTION:  Download and format germlines from the IMGT website
#
# Original work:
#        Author:  Mohamed Uduman, Jason Anthony Vander Heiden
#          Date:  2017.07.03
#       License:  AGPL-3
#        Source:  https://bitbucket.org/kleinstein/immcantation/src/master/scripts/fetch_imgtdb.sh
#Current source:  https://github.com/immcantation/immcantation/blob/master/scripts/fetch_imgtdb.sh
#
# Extended work:
#   Modified by:  Jonas Schuck, jschuckdev@gmail.com
#    BUG-REPORT:  https://github.com/AGImkeller/LongAIRR/issues
#          Date:  2024.08.21
#
#          NOTE: This file is a modified version of software distributed by the
#                Immcantation project under the GNU Affero General Public License,
#                version 3. This modified file remains licensed under AGPL-3.0-only
#                and is not covered by LongAIRR's Apache-2.0 license.
#
#================================================================#


#===========install dependencies for all db-install scripts====================#

# Define required packages
declare -A required_packages
required_packages[biopython]="1.83"
required_packages[packaging]=""

# Function to check if a package is installed and meets the required version
check_and_install() {
    package=$1
    required_version=$2

    # Check if the package is installed
    if python -c "import $package" 2>/dev/null; then
        if [[ -n "$required_version" ]]; then
            installed_version=$(python -c "import $package; print($package.__version__)" 2>/dev/null)
            if [[ "$installed_version" != "$required_version" ]]; then
                echo "Version mismatch: $package $installed_version (required: $required_version). Reinstalling..."
                pip install --upgrade "$package==$required_version"
            else
                echo "$package is already installed and up-to-date ($installed_version)."
            fi
        else
            echo "$package is already installed."
        fi
    else
        echo "Installing $package..."
        if [[ -n "$required_version" ]]; then
            pip install "$package==$required_version"
        else
            pip install "$package"
        fi
    fi
}

# Loop through required packages and install them if needed
for package in "${!required_packages[@]}"; do
    check_and_install "$package" "${required_packages[$package]}"
done

#===================================================


# Default argument values
OUTDIR="."
OUTDIR_SET="false"
INPUT_SPECIES=()

# Show general help message
show_help () {
    echo "Usage: $(basename $0) [OPTIONS] [--species species1,species2,...]"
    echo "  -o  Output directory for downloaded files. Defaults to current directory."
    echo "  --species  Comma-separated list of species to download. Valid species are:"
    echo "             human, mouse, rat, rabbit, rhesus_monkey"
    echo "  -h  This message."
    echo
    echo "Example:"
    echo "  $(basename $0) -o /path/to/output --species human,mouse"
}

# Process command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -o)
            if [ -n "$2" ]; then
                OUTDIR=$2
                OUTDIR_SET=true
                shift 2
            else
                echo "-o option requires an argument." >&2
                exit 1
            fi
            ;;
        --species)
            if [ -n "$2" ]; then
                IFS=',' read -ra INPUT_SPECIES <<< "$2"
                shift 2
            else
                echo "--species option requires an argument." >&2
                exit 1
            fi
            ;;
        -h)
            show_help
            exit 0
            ;;
        *)
            echo "Invalid option: $1" >&2
            show_help
            exit 1
            ;;
    esac
done

# Info
REPERTOIRE="imgt"
DATE=$(date +"%Y.%m.%d")

# Create array where keys are species names and values are query strings
# Keys are checked/valid input values (if multiple then comma-separated)
declare -A SPECIES_QUERY
declare -A SPECIES_REPLACE

SPECIES_QUERY=(
    ["human"]="Homo+sapiens"
    ["mouse"]="Mus"
    ["rat"]="Rattus+norvegicus"
    ["rabbit"]="Oryctolagus+cuniculus"
    ["rhesus_monkey"]="Macaca+mulatta"
)

SPECIES_REPLACE=(
    ["human"]="s/Homo sapiens/Homo_sapiens/g"
    ["mouse"]="s/Mus musculus/Mus_musculus/g"
    ["rat"]="s/Rattus norvegicus/Rattus_norvegicus/g"
    ["rabbit"]="s/Oryctolagus cuniculus/Oryctolagus_cuniculus/g"
    ["rhesus_monkey"]="s/Macaca mulatta/Macaca_mulatta/g"
)

# Filter the SPECIES_QUERY and SPECIES_REPLACE arrays if specific species were provided
declare -A FILTERED_QUERY
declare -A FILTERED_REPLACE

if [ ${#INPUT_SPECIES[@]} -gt 0 ]; then
    for species in "${INPUT_SPECIES[@]}"; do
        if [[ -n "${SPECIES_QUERY[$species]}" ]]; then
            FILTERED_QUERY[$species]="${SPECIES_QUERY[$species]}"
            FILTERED_REPLACE[$species]="${SPECIES_REPLACE[$species]}"
        fi
    done
else
    FILTERED_QUERY=("${SPECIES_QUERY[@]}")
    FILTERED_REPLACE=("${SPECIES_REPLACE[@]}")
fi

echo "Filtered Species Queries: ${FILTERED_QUERY[@]}"
echo "Filtered Species Replacements: ${FILTERED_REPLACE[@]}"

echo "$FILTERED_QUERY"
echo "$FILTERED_REPLACE"

WGET="wget"
if ! command -v wget &> /dev/null; then
    if ! command -v wget2 &> /dev/null; then
        echo "wget or wget2 not found."
        exit 1
    else
        WGET=wget2
    fi
fi

# Counter for loop iteration, used for getting the right values of SPECIES_REPLACE
COUNT=0
# For each species

for SPECIES in "${!FILTERED_QUERY[@]}"; do
    echo $SPECIES
    KEY="$SPECIES"
    VALUE="${FILTERED_QUERY[$KEY]}"
    REPLACE_VALUE="${FILTERED_REPLACE[$KEY]}"
    echo "Downloading ${KEY} repertoires into ${OUTDIR}"

	# Download VDJ
	echo "|- VDJ regions"
    FILE_PATH="${OUTDIR}/${KEY}/vdj"
    FILE_PATH_AA="${OUTDIR}/${KEY}/vdj_aa"
    FILE_PATH_LV="${OUTDIR}/${KEY}/leader_vexon"
    mkdir -p $FILE_PATH $FILE_PATH_AA $FILE_PATH_LV

    # VDJ Ig
    echo "|---- Ig"
    for CHAIN in IGHV IGHD IGHJ IGKV IGKJ IGLV IGLJ
    do
        URL="https://www.imgt.org/genedb/GENElect?query=7.1+${CHAIN}&species=${VALUE}"
        FILE_NAME="${FILE_PATH}/${REPERTOIRE}_${KEY}_${CHAIN}.fasta"
        TMP_FILE="${FILE_NAME}.tmp"
        #echo $URL
        ${WGET} $URL -O $TMP_FILE -q
        awk '/<pre>/{i++}/<\/pre>/{j++}{if(j==2){exit}}{if(i==2 && j==1 && $0!~"^<pre>"){print}}' $TMP_FILE > $FILE_NAME

        # Check file exists and is not empty
        if [ ! -s "$FILE_NAME" ]
        then
            echo "IMGT Fasta file does not exist, or is empty. Is the IMGT server online?"
            exit 1
        fi

        # Make sed command work also for mac, see: https://stackoverflow.com/a/44864004
        sed -i.bak "$REPLACE_VALUE" $FILE_NAME && rm $FILE_NAME.bak
        rm $TMP_FILE
    done

    # Artificial spliced leader and V exon for Ig
    for CHAIN in IGHV IGKV IGLV
    do
        URL="https://www.imgt.org/genedb/GENElect?query=8.1+${CHAIN}&species=${VALUE}&IMGTlabel=L-PART1+V-EXON"
        FILE_NAME="${FILE_PATH_LV}/${REPERTOIRE}_lv_${KEY}_${CHAIN}.fasta"
        TMP_FILE="${FILE_NAME}.tmp"
        #echo $URL
        ${WGET} $URL -O $TMP_FILE -q
        awk '/<pre>/{i++}/<\/pre>/{j++}{if(j==2){exit}}{if(i==2 && j==1 && $0!~"^<pre>"){print}}' $TMP_FILE > $FILE_NAME

        # Check file exists and is not empty
        if [ ! -s "$FILE_NAME" ]
        then
            echo "IMGT Fasta file does not exist, or is empty. Is the IMGT server online?"
            exit 1
        fi

        # Make sed command work also for mac, see: https://stackoverflow.com/a/44864004
        sed -i.bak "$REPLACE_VALUE" $FILE_NAME && rm $FILE_NAME.bak
        rm $TMP_FILE
    done

    # V amino acid for Ig
    for CHAIN in IGHV IGKV IGLV
    do
        URL="https://www.imgt.org/genedb/GENElect?query=7.3+${CHAIN}&species=${VALUE}"
        FILE_NAME="${FILE_PATH_AA}/${REPERTOIRE}_aa_${KEY}_${CHAIN}.fasta"
        TMP_FILE="${FILE_NAME}.tmp"
        #echo $URL
        ${WGET} $URL -O $TMP_FILE -q
        awk '/<pre>/{i++}/<\/pre>/{j++}{if(j==2){exit}}{if(i==2 && j==1 && $0!~"^<pre>"){print}}' $TMP_FILE > $FILE_NAME

        # Check file exists and is not empty
        if [ ! -s "$FILE_NAME" ]
        then
            echo "IMGT Fasta file does not exist, or is empty. Is the IMGT server online?"
            exit 1
        fi

        # Make sed command work also for mac, see: https://stackoverflow.com/a/44864004
        sed -i.bak "$REPLACE_VALUE" $FILE_NAME && rm $FILE_NAME.bak
        rm $TMP_FILE
    done

    # VDJ TCR
    echo "|---- TCR"
    for CHAIN in TRAV TRAJ TRBV TRBD TRBJ TRDV TRDD TRDJ TRGV TRGJ
    do
        URL="https://www.imgt.org/genedb/GENElect?query=7.1+${CHAIN}&species=${VALUE}"
        FILE_NAME="${FILE_PATH}/${REPERTOIRE}_${KEY}_${CHAIN}.fasta"
        TMP_FILE="${FILE_NAME}.tmp"
        #echo $URL
        ${WGET} $URL -O $TMP_FILE -q
        awk '/<pre>/{i++}/<\/pre>/{j++}{if(j==2){exit}}{if(i==2 && j==1 && $0!~"^<pre>"){print}}' $TMP_FILE > $FILE_NAME

        # Check file exists and is not empty
        if [ ! -s "$FILE_NAME" ]
        then
            echo "IMGT Fasta file does not exist, or is empty. Is the IMGT server online?"
            exit 1
        fi

        sed -i.bak "$REPLACE_VALUE" $FILE_NAME && rm $FILE_NAME.bak
        rm $TMP_FILE
    done

    # Artificial spliced leader and V exon for TCR
    for CHAIN in TRAV TRBV TRDV TRGV
    do
        URL="https://www.imgt.org/genedb/GENElect?query=8.1+${CHAIN}&species=${VALUE}&IMGTlabel=L-PART1+V-EXON"
        FILE_NAME="${FILE_PATH_LV}/${REPERTOIRE}_lv_${KEY}_${CHAIN}.fasta"
        TMP_FILE="${FILE_NAME}.tmp"
        #echo $URL
        ${WGET} $URL -O $TMP_FILE -q
        awk '/<pre>/{i++}/<\/pre>/{j++}{if(j==2){exit}}{if(i==2 && j==1 && $0!~"^<pre>"){print}}' $TMP_FILE > $FILE_NAME

        # Check file exists and is not empty
        if [ ! -s "$FILE_NAME" ]
        then
            echo "IMGT Fasta file does not exist, or is empty. Is the IMGT server online?"
            exit 1
        fi

        # Make sed command work also for mac, see: https://stackoverflow.com/a/44864004
        sed -i.bak "$REPLACE_VALUE" $FILE_NAME && rm $FILE_NAME.bak
        rm $TMP_FILE
    done

    # V amino acid for TCR
    for CHAIN in TRAV TRBV TRDV TRGV
    do
        URL="https://www.imgt.org/genedb/GENElect?query=7.3+${CHAIN}&species=${VALUE}"
        FILE_NAME="${FILE_PATH_AA}/${REPERTOIRE}_aa_${KEY}_${CHAIN}.fasta"
        TMP_FILE="${FILE_NAME}.tmp"
        #echo $URL
        ${WGET} $URL -O $TMP_FILE -q
        awk '/<pre>/{i++}/<\/pre>/{j++}{if(j==2){exit}}{if(i==2 && j==1 && $0!~"^<pre>"){print}}' $TMP_FILE > $FILE_NAME

        # Check file exists and is not empty
        if [ ! -s "$FILE_NAME" ]
        then
            echo "IMGT Fasta file does not exist, or is empty. Is the IMGT server online?"
            exit 1
        fi

        sed -i.bak "$REPLACE_VALUE" $FILE_NAME && rm $FILE_NAME.bak
        rm $TMP_FILE
    done

	# Download leaders
    echo "|- Spliced leader regions"
    FILE_PATH="${OUTDIR}/${KEY}/leader"
    mkdir -p $FILE_PATH

    # Spliced leader Ig
    echo "|---- Ig"
    for CHAIN in IGH IGK IGL
    do
        URL="https://www.imgt.org/genedb/GENElect?query=8.1+${CHAIN}V&species=${VALUE}&IMGTlabel=L-PART1+L-PART2"
        FILE_NAME="${FILE_PATH}/${REPERTOIRE}_${KEY}_${CHAIN}L.fasta"
        TMP_FILE="${FILE_NAME}.tmp"
        #echo $URL
        ${WGET} $URL -O $TMP_FILE -q
        awk '/<pre>/{i++}/<\/pre>/{j++}{if(j==2){exit}}{if(i==2 && j==1 && $0!~"^<pre>"){print}}' $TMP_FILE > $FILE_NAME

        # Check file exists and is not empty
        if [ ! -s "$FILE_NAME" ]
        then
            echo "IMGT Fasta file does not exist, or is empty. Is the IMGT server online?"
            exit 1
        fi

        sed -i.bak "$REPLACE_VALUE" $FILE_NAME && rm $FILE_NAME.bak
        rm $TMP_FILE
    done

    # Spliced leader TCR
    echo "|---- TCR"
    for CHAIN in TRA TRB TRG TRD
    do
        URL="https://www.imgt.org/genedb/GENElect?query=8.1+${CHAIN}V&species=${VALUE}&IMGTlabel=L-PART1+L-PART2"
        FILE_NAME="${FILE_PATH}/${REPERTOIRE}_${KEY}_${CHAIN}L.fasta"
        TMP_FILE="${FILE_NAME}.tmp"
        #echo $URL
        ${WGET} $URL -O $TMP_FILE -q
        awk '/<pre>/{i++}/<\/pre>/{j++}{if(j==2){exit}}{if(i==2 && j==1 && $0!~"^<pre>"){print}}' $TMP_FILE > $FILE_NAME

        # Check file exists and is not empty
        if [ ! -s "$FILE_NAME" ]
        then
            echo "IMGT Fasta file does not exist, or is empty. Is the IMGT server online?"
            exit 1
        fi

        sed -i.bak "$REPLACE_VALUE" $FILE_NAME && rm $FILE_NAME.bak
        rm $TMP_FILE
    done

	# Download constant regions
    echo "|- Spliced constant regions"
    FILE_PATH="${OUTDIR}/${KEY}/constant/"
    mkdir -p $FILE_PATH

    # Constant Ig
    echo "|---- Ig"
    for CHAIN in IGHC IGKC IGLC
    do
        # IMGT does not have artificially spliced IGKC / IGLC for multiple species
        if [ "$CHAIN" == "IGHC" ]; then
            QUERY=14.1
        else
            QUERY=7.5
        fi

        URL="https://www.imgt.org/genedb/GENElect?query=${QUERY}+${CHAIN}&species=${VALUE}"
        FILE_NAME="${FILE_PATH}/${REPERTOIRE}_${KEY}_${CHAIN}.fasta"
        TMP_FILE="${FILE_NAME}.tmp"
        #echo $URL
        ${WGET} $URL -O $TMP_FILE -q
        awk '/<pre>/{i++}/<\/pre>/{j++}{if(j==2){exit}}{if(i==2 && j==1 && $0!~"^<pre>"){print}}' $TMP_FILE > $FILE_NAME

        # Check file exists and is not empty
        if [ ! -s "$FILE_NAME" ]
        then
            echo "IMGT Fasta file does not exist, or is empty. Is the IMGT server online?"
            exit 1
        fi

        sed -i.bak "$REPLACE_VALUE" $FILE_NAME && rm $FILE_NAME.bak
        rm $TMP_FILE
    done

    # Constant for TCR
    echo "|---- TCR"
    for CHAIN in TRAC TRBC TRGC TRDC
    do
        URL="https://www.imgt.org/genedb/GENElect?query=14.1+${CHAIN}&species=${VALUE}"
        FILE_NAME="${FILE_PATH}/${REPERTOIRE}_${KEY}_${CHAIN}.fasta"
        TMP_FILE="${FILE_NAME}.tmp"
        #echo $URL
        ${WGET} $URL -O $TMP_FILE -q
        awk '/<pre>/{i++}/<\/pre>/{j++}{if(j==2){exit}}{if(i==2 && j==1 && $0!~"^<pre>"){print}}' $TMP_FILE > $FILE_NAME

        # Check file exists and is not empty
        if [ ! -s "$FILE_NAME" ]
        then
            echo "IMGT Fasta file does not exist, or is empty. Is the IMGT server online?"
            exit 1
        fi

        sed -i.bak "$REPLACE_VALUE" $FILE_NAME && rm $FILE_NAME.bak
        rm $TMP_FILE
    done

    echo ""
    ((COUNT++))
done

# Write download info
INFO_FILE=${OUTDIR}/IMGT.yaml
echo -e "source:  https://www.imgt.org/genedb" > $INFO_FILE
echo -e "date:    ${DATE}" >> $INFO_FILE
echo -e "species:" >> $INFO_FILE
for Q in ${SPECIES_QUERY[@]}
do
    echo -e "    - ${Q}" >> $INFO_FILE
done
