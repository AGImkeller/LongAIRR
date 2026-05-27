#!/usr/bin/env python3

import argparse

#================================================================#
#
#        Script:  longairr_header_metadata.py
#         Usage:  Internal script used in 'longairr.sh/longairr collapse'
#
#   DESCRIPTION:  Enumerates sequences and writes consensus information into the
#                 FASTA header of each sequence. For each record, a new header
#                 of the form: 
#                 `>seqN|GROUP=<SPBCUMI or UMI>|CONSCOUNT=..|N_ORIG=.. |N_KEEP=.. |UMI=<barcode>`
#                 is generated. If --spatial is set, spatial barcodes (SPBC)
#                 and their counts (PRCOUNT) are also appended.
#
#        AUTHOR:  Jonas Schuck, jschuckdev@gmail.com
#    BUG-REPORT:  https://github.com/AGImkeller/LongAIRR/issues
#
#================================================================#


def parse_header_fields(header_line):
    parts = header_line.strip().split("|")
    barcode = parts[0][1:]  # remove '>'

    fields = {}
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            fields[key] = value

    return barcode, fields


def build_header(seq_count, barcode, fields, library):
    new_header = f">seq{seq_count}|GROUP={barcode}"

    # common fields
    if "CONSCOUNT" in fields:
        new_header += f"|CONSCOUNT={fields['CONSCOUNT']}"
    if "N_ORIG" in fields:
        new_header += f"|N_ORIG={fields['N_ORIG']}"
    if "N_KEEP" in fields:
        new_header += f"|N_KEEP={fields['N_KEEP']}"
    if "UMI" in fields:
        new_header += f"|UMI={fields['UMI']}"

    if library == "bulk":
        return new_header

    # SPBC is carried through BuildConsensus via --pf SPBC
    if "PRIMER" in fields:
        new_header += f"|SPBC={fields['PRIMER']}"
    elif "SPBC" in fields:
        new_header += f"|SPBC={fields['SPBC']}"

    if "PRCOUNT" in fields:
        new_header += f"|PRCOUNT={fields['PRCOUNT']}"

    if "X" in fields:
        new_header += f"|X={fields['X']}"
    if "Y" in fields:
        new_header += f"|Y={fields['Y']}"

    if library == "visium":
        return new_header

    if library == "visiumhd":
        if "BC1" in fields:
            new_header += f"|BC1={fields['BC1']}"
        if "BC2" in fields:
            new_header += f"|BC2={fields['BC2']}"
        if "SPBC10X" in fields:
            new_header += f"|SPBC10X={fields['SPBC10X']}"

    return new_header


def process_fasta(input_file, output_file, library="bulk"):
    seq_count = 1

    with open(input_file, "r") as infile, open(output_file, "w") as outfile:
        for line in infile:
            if line.startswith(">"):
                barcode, fields = parse_header_fields(line)
                new_header = build_header(seq_count, barcode, fields, library)
                outfile.write(new_header + "\n")
                seq_count += 1
            else:
                outfile.write(line)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Rewrite FASTA headers after consensus building."
    )
    parser.add_argument("--input", required=True, help="Input FASTA")
    parser.add_argument("-o", "--output", required=True, help="Output FASTA")
    parser.add_argument("--library", choices=["bulk", "visium", "visiumhd"], default="visium", help="Library type (default: visium)")
    return parser.parse_args()


def main():
    args = parse_args()
    process_fasta(args.input, args.output, library=args.library)


if __name__ == "__main__":
    main()