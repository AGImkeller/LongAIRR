#!/bin/bash

#================================================================#
#
#        Script:  longairr_utils.sh
#         Usage:  Internal script sourced by longairr.sh
#
#   DESCRIPTION:  Script contains documentation and functions for redundant parts
#                 that are frequently used in the main longairr.sh script
#
#        AUTHOR:  Jonas Schuck, jschuckdev@gmail.com
#    BUG-REPORT:  https://github.com/AGImkeller/LongAIRR/issues
#
#================================================================#


#--------general util functions-------#

#######################################
# Validate boolean parameters
# 
# Ensures that input parameters accepting TRUE/FALSE values are correctly formatted
#
# Arguments:
#   $1 - Parameter name (for error message clarity)
#   $2 - Parameter value (expected: TRUE or FALSE)
#
# Exits:
#   Exits with error if the provided value is not TRUE or FALSE.
#######################################
validate_boolean_parameters() {
  local parameter_name="$1"
  local parameter_value="$2"
  if [[ "${parameter_value}" != "TRUE" && "${parameter_value}" != "FALSE" ]]; then
    echo "Error: Invalid value for \"${parameter_name}\". Must be TRUE or FALSE."
    echo "Use 'nanoairr --help' for overall usage or function-specific help, e.g., 'nanoairr filter --help'."
    exit 1
  fi
}


#######################################
# Log messages with timestamps
# 
# Formats and writes log messages to both console and a log file.
#
# Arguments:
#   $1 - Log level (INFO, WARNING, ERROR)
#   $2 - LongAIRR step/module name
#   $3 - Log message
#   $4 - Path to log file
#
# Output:
#   Logs messages in the format: [TIMESTAMP] [LEVEL] [STEP] MESSAGE
#######################################
log_message() {
  local level="$1"      # Log level: INFO, WARNING, ERROR
  local step="$2"
  local message="$3"    # Log message
  local log_file="$4"   # Path to log file

  # Get current timestamp
  local timestamp
  timestamp=$(date +"%Y-%m-%d %H:%M:%S")

  # Format the log message with timestamp and level
  local formatted_message="\n[${timestamp}] [${level}] [${step}] ${message}"

  # Append the message to log file
  if [[ -n "${log_file}" ]]; then
    echo -e "${formatted_message}" >> "${log_file}"
  fi
  echo -e "${formatted_message}"
}


#######################################
# Display progress bar
# 
# Generates a dynamic progress bar for tracking task completion.
#
# Arguments:
#   $1 - Current step
#   $2 - Total steps
#
#######################################
progress_bar() {
  local current=$1
  local total=$2
  local width=30  # Width of the progress bar

  # Calculate progress percentage and completed segments
  local percent=$((current * 100 / total))
  local filled=$((current * width / total))
  local empty=$((width - filled))

  # Generate the progress bar
  local bar=$(printf "%0.s#" $(seq 1 $filled))
  local spaces=$(printf "%0.s-" $(seq 1 $empty))

  # Print the progress bar to stdout
  if [[ "${current}" -eq "${total}" ]]; then
    # If complete, print a new line after the progress bar
    printf "\r[%s%s] %d%%\n" "${bar}" "${spaces}" "${percent}"
  else
    # Otherwise, update the progress bar on the same line
    printf "\r[%s%s] %d%%" "${bar}" "${spaces}" "${percent}"
  fi
}


#######################################
# Update progress bar
# 
# Increments the progress bar by updating the current step count.
#
# Arguments:
#   $1 - Current step
#   $2 - Total steps
#
#######################################
update_progress() {
  local current=$1
  local total=$2

  ((current_step++))
  progress_bar ${current_step} ${total}
}


#-----------basecalling utils---------#

#######################################
# Process Simplex/Duplex Reads
# 
# Filters simplex/duplex reads from a BAM file and generates corresponding FASTA/FASTQ files if specified.
#
# Arguments:
#   $1 - Dorado flag (0 for simplex, 1 for duplex)
#   $2 - Input BAM file path
#   $3 - Output BAM file path
#   $4 - Output FASTQ file path
#   $5 - Output FASTA file path
#   $6 - FASTA flag (TRUE to generate FASTA, FALSE otherwise)
#
# Output:
#   - Read-type BAM file
#   - FASTQ file (converted from BAM)
#   - FASTA file (if FASTA flag is TRUE)
#
#######################################
process_simplex_duplex() {
  local dorado_flag="$1"
  local input_bam="$2"
  local output_bam="$3"
  local output_fastq="$4"
  local output_fasta="$5"
  local fasta_flag="$6"

  # Process if DORADO_FLAG is 0 (simplex) or 1 (duplex)
  # NOTE: Find the reference for third party software 'samtools' in '/vignette.software_references.md`
  samtools view -b -h -d "dx:$dorado_flag" "${input_bam}" > "${output_bam}" || {
    log_message "ERROR" "longairr basecalling" \
      "Failed to filter BAM for read type \"${dorado_flag}\"." \
      "${log_file}"
    exit 1
  }

  # Generate fastq from bam
  samtools bam2fq "${output_bam}" > "${output_fastq}" || {
    log_message "ERROR" "longairr basecalling" \
      "Failed to convert BAM to FASTQ" \
      "${log_file}"
    exit 1
  }

  # Generate additional fasta if specified
  # NOTE: Find the reference for third party software 'seqkit' in '/vignette.software_references.md`
  if [[ "${fasta_flag}" == "TRUE" ]]; then
    seqkit fq2fa "${output_fastq}" -o "${output_fasta}" || {
      log_message "ERROR" "longairr basecalling" \
        "Failed to convert FASTQ to FASTA" \
        "${log_file}"
      exit 1
    }
  fi
}
