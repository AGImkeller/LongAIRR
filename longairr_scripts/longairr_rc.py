#!/usr/bin/env python3

import argparse
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord

#================================================================#
#
#        Script:  longairr_rc.py
#         Usage:  Internal script used in 'longairr demux' and 'longairr collapse'
#
#   DESCRIPTION:  Script to generate reverse-complement of reads that
#                 failed to match the anchor/barcode sequences
#
#        AUTHOR:  Jonas Schuck, jschuckdev@gmail.com
#    BUG-REPORT:  https://github.com/AGImkeller/LongAIRR/issues
#
#================================================================#


def translate_to_reverse_complement(input_file, output_file):
    # Read sequences from input FASTA file
    records = SeqIO.parse(input_file, "fasta")

    # Initialize a list to store reverse complement sequences
    rc_records = []

    # Translate sequences to their reverse complement
    for record in records:
        seq = record.seq.reverse_complement()
        rc_record = SeqRecord(seq, id=record.id, description=record.description)
        rc_records.append(rc_record)

    # Write reverse complement sequences to output FASTA file
    SeqIO.write(rc_records, output_file, "fasta")


def parse_args():
    parser = argparse.ArgumentParser(description="Translate sequences in a FASTA file to their reverse complement.")
    parser.add_argument("-i", "--input", required=True, help="Input FASTA file path")
    parser.add_argument("-o", "--output", required=True, help="Output FASTA file path")

    return parser.parse_args()


def main():
    args = parse_args()
    translate_to_reverse_complement(args.input, args.output)


if __name__ == "__main__":
    main()
