#!/usr/bin/env python3

import argparse
import sys
import re
import os

#================================================================#
#
#        Script:  nanoairr_trim_umi.py
#         Usage:  Internal script used in 'nanoairr.sh/nanoairr umis'
#
#   DESCRIPTION:  Script that modifies the barcode in the BARCODE slot
#                 of the header based on the '--forward' parameter and specified length.
#                 If forward is "TRUE", take the last 'length' characters.
#                 Otherwise, take the first 'length' characters.
#
#        AUTHOR:  Jonas Schuck, jschuckdev@gmail.com
#    BUG-REPORT:  https://github.com/AGImkeller/AIRR_workflow/issues
#
#================================================================#

# Function performing the actual trimming
def modify_barcode(barcode, length, forward):
    if len(barcode) < length:
        return None  # If barcode is shorter than specified length, return None
    # If forward TRUE take the sequence from the end of the BARCODE sequence of '--length', else take the sequence from the start
    return barcode[-length:] if forward == "TRUE" else barcode[:length]

# Main function parsing every sequence of the input FASTA file and trimming the sequence present in the BARCODE slot
def trim_umis(input_file, output_file, length, forward, verbose):
    filtered_count = 0
    # Process the input file
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            if line.startswith(">"):
                # Extract the BARCODE value
                barcode_match = re.search(r'\|BARCODE=(\w*)', line)
                if barcode_match:
                    barcode = barcode_match.group(1)
                    # Modify the BARCODE based on the forward parameter
                    new_barcode = modify_barcode(barcode, length, forward)
                    if new_barcode is None:
                        filtered_count += 1
                        continue  # Skip writing this header if barcode is too short
                    # Replace the BARCODE value with the new one
                    line = re.sub(r'BARCODE=\w+', f'UMI={new_barcode}', line)
            outfile.write(line)

    # Print the number of filtered sequences if --verbose set to true
    if verbose == "TRUE":
        print("\n" + f"Number of sequences filtered out due to a UMI length below {length} bp: {filtered_count}" + "\n\n")


def parse_args():
    parser = argparse.ArgumentParser(description="Modify and trim the UMI sequence specified in the BARCODE slot of each sequence")
    parser.add_argument("--length", required=True, type=int, default=12, help="Specify the umi/barcode length (default=12 bp)")
    parser.add_argument("--forward", choices=["TRUE", "FALSE"], default="TRUE", help="Specify if the barcode should be taken from the end (true) or the start (false) of the sequence present in the BARCODE slot (default: TRUE)")
    parser.add_argument("-o", "--output", required=True,  default="output.fasta", help="Specify the output file")
    parser.add_argument("-i", "--input", required=True, help="Input FASTA file")
    parser.add_argument("--verbose", choices=["TRUE", "FALSE"], default="FALSE", help="Print the number of filtered sequences (default=FALSE)")

    return parser.parse_args()


def main():
    args = parse_args()

    # Pass arguments and run main function
    trim_umis(args.input, args.output, args.length, args.forward, args.verbose)


if __name__ == "__main__":
    main()
