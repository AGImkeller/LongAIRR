#!/usr/bin/env python3

import argparse
import itertools
import gzip
from Bio import SeqIO
from Bio.Seq import Seq


#================================================================#
#
#        Script:  longairr_spbc_umi.py
#         Usage:  Internal script used in 'longairr.sh/longairr collapse'
#
#   DESCRIPTION:  Annotates spatial barcode / UMI information in anchor-cut reads.
#
#                 Supports two spatial modes:
#
#                 1) visium
#                    - fixed SPBC length
#                    - fixed UMI length
#                    - one SPBC whitelist
#                    - exact match or optional mismatch-based correction
#                    - header emits: SPBC, UMI, SPBCUMI
#
#                 2) visium_hd
#                    - exact matching only
#                    - two whitelist files (BC1 and BC2)
#                    - fixed base UMI length of 9
#                    - tries offsets 0/1/2
#                    - offset nt are included in emitted UMI
#                    - header emits: UMI, BC1, BC2, SPBC, UMISPBC, X, Y, SPBC10X
#
#        AUTHOR:  Jonas Schuck, jschuckdev@gmail.com
#    BUG-REPORT:  https://github.com/AGImkeller/AIRR_workflow/issues
#
#================================================================#


# ----------------------------
# Generic helpers
# ----------------------------

def parse_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def open_txt(path, mode="rt"):
    return open(path, mode)


def write_failed_record(record, failed_handle, reason):
    if failed_handle is not None:
        record.description = reason
        SeqIO.write(record, failed_handle, "fasta")


# ----------------------------
# Classic Visium helpers
# ----------------------------

# Load Visium SPBC whitelist and optional coordinates [visium_v1.txt]
def load_visium_spbc_info(file_path):
    spbc_info = {}
    valid_spbc_set = set()

    with open_txt(file_path, "rt") as f:
        for line in f:
            fields = line.strip().split()
            if not fields:
                continue

            spbc = fields[0]
            if not spbc:
                continue

            x, y = None, None
            if len(fields) >= 3:
                try:
                    x = int(fields[1])
                    y = int(fields[2])
                except ValueError:
                    raise ValueError(
                        f"Could not parse x/y coordinates from whitelist line: {line.strip()}"
                    )

            spbc_info[spbc] = (x, y)
            valid_spbc_set.add(spbc)

    return spbc_info, valid_spbc_set


# Function used when allowing spbc-mismatches in visium
# Generate all sequences at exact Hamming distance k for each seq
# Faster than pairwise approach of all read-spbcs to all valid-spbcs
def generate_neighbors_at_distance(seq, k, alphabet=("A", "C", "G", "T")):
    if k == 0:
        yield seq
        return

    seq_list = list(seq)

    # choose k positions to mutate
    for positions in itertools.combinations(range(len(seq)), k):
        # for each combination of replacement bases at those positions
        for bases in itertools.product(alphabet, repeat=k):
            # ensure all chosen positions actually change (so distance is exactly k)
            if all(b != seq_list[pos] for b, pos in zip(bases, positions)):
                mutated = seq_list.copy()
                for b, pos in zip(bases, positions):
                    mutated[pos] = b
                yield "".join(mutated)

# Compute hamming distance between two sequences by element-wise comparison
def hamming_distance(seq1, seq2, allowed_mismatches):
    mismatches = 0
    # if there are more mismatches than allowed, stop comparison and return (saves time)
    for el1, el2 in zip(seq1, seq2):
        if el1 != el2:
            mismatches += 1
            if mismatches > allowed_mismatches:
                return mismatches
    return mismatches


def find_closest_spbc(spbc,
                      valid_spbc_set,
                      mismatch_fraction,
                      best_match_cache,
                      max_enum_mismatches=3):

    # Per-SPBC cache: saves best_matches
    if spbc in best_match_cache:
        return best_match_cache[spbc]

    length = len(spbc)
    allowed_mismatches = int(length * mismatch_fraction)

    # exact match
    if allowed_mismatches == 0:
        closest = spbc if spbc in valid_spbc_set else None
        best_match_cache[spbc] = closest
        return closest

    # for errors below a error_threshold, use neighbour approach
    if allowed_mismatches <= max_enum_mismatches:
        for k in range(0, allowed_mismatches + 1):
            candidates = []

            for neighbor in generate_neighbors_at_distance(spbc, k):
                if neighbor in valid_spbc_set:
                    candidates.append(neighbor)

            if candidates:
                # deterministic tie-breaking: lexicographically smallest candidate
                closest = min(candidates)
                best_match_cache[spbc] = closest
                return closest

        # no neighbor within allowed mismatches
        best_match_cache[spbc] = None
        return None

    # Fallback: for very large number of allowed errors, use pairwise spbc-valid spbc comparison
    closest_spbc = None
    min_distance = allowed_mismatches + 1

    for valid_spbc in valid_spbc_set:
        d = hamming_distance(spbc, valid_spbc, allowed_mismatches)
        if d <= allowed_mismatches and d < min_distance:
            min_distance = d
            closest_spbc = valid_spbc

    best_match_cache[spbc] = closest_spbc
    return closest_spbc


# ----------------------------
# Visium HD helpers
# ----------------------------

# Load Visium HD SPBC whitelists for Bc1 and Bc2
def load_sequence_list(file_path):
    seqs = []
    with open_txt(file_path, "rt") as f:
        for line in f:
            seq = line.split()[0]
            if seq:
                seqs.append(seq)
    return seqs


# Annotation of UMI and SPBC in Visium v1 long reads
class VisiumDecoder:
    def __init__(self, spbc_file, spbc_length=16, umi_length=12, mismatch_fraction=0.0):
        self.spbc_length = spbc_length
        self.umi_length = umi_length
        self.mismatch_fraction = mismatch_fraction
        #spbc info contains spbc - coord relations; valid_spbc_set a set of only the coords
        self.spbc_info, self.valid_spbc_set = load_visium_spbc_info(spbc_file)
        self.best_match_cache = {}

        # log info 
        if mismatch_fraction > 0.0:
            logging_allowed = int(spbc_length * mismatch_fraction)
            print(
                f"Visium SPBC filtering with mismatches enabled. "
                f"Example: SPBC length {spbc_length} - allowed mismatches {logging_allowed}."
            )

    # function to annotate reads (read starts directly after truseq)
    def decode(self, sequence):
        if len(sequence) < (self.spbc_length + self.umi_length):
            return None
        # annotate spbc and umi
        observed_spbc = sequence[:self.spbc_length]
        umi = sequence[self.spbc_length:self.spbc_length + self.umi_length]
        # Exact match // no mismatches
        if self.mismatch_fraction == 0.0:
            corrected_spbc = observed_spbc if observed_spbc in self.valid_spbc_set else None
        else: # mismatches allowed, look for closest spbc in the list
            corrected_spbc = find_closest_spbc(
                observed_spbc,
                self.valid_spbc_set,
                self.mismatch_fraction,
                self.best_match_cache
            )

        if corrected_spbc is None:
            return None
        # length that will be trimmed off (cut = TRUE)
        trim_len = self.spbc_length + self.umi_length
        # get coords from spbc_info
        x, y = self.spbc_info.get(corrected_spbc, (None, None))
        # add all info to header
        header_fields = [
            f"SPBC={corrected_spbc}",
            f"UMI={umi}",
            f"SPBCUMI={corrected_spbc}{umi}",
        ]

        if x is not None and y is not None:
            header_fields.extend([
                f"X={x}",
                f"Y={y}",
            ])

        return {
            "mode": "visium",
            "trim_len": trim_len,
            "header_fields": header_fields,
        }


# Annotation of UMI and SPBC (Bc1 + Bc2) in Visium HD v1 long reads
class VisiumHDDecoder:
    def __init__(self, bc1_file, bc2_file, umi_base_length=9, offsets=(0, 1, 2),
        split_order=((15, 14), (15, 15), (16, 14), (16, 15)), hd_bins="002um"):
        
        self.bc1_list = load_sequence_list(bc1_file)
        self.bc2_list = load_sequence_list(bc2_file)

        self.bc1_set_by_len = {}
        self.bc2_set_by_len = {}
        # sort bc1 and bc2 spbcs into sets by length (14, 15, 16)
        for seq in self.bc1_list:
            self.bc1_set_by_len.setdefault(len(seq), set()).add(seq)
        for seq in self.bc2_list:
            self.bc2_set_by_len.setdefault(len(seq), set()).add(seq)
        # add indices from the original list [bc1=x=row index; bc2=y=row index]
        self.bc1_index = {seq: i for i, seq in enumerate(self.bc1_list)}
        self.bc2_index = {seq: i for i, seq in enumerate(self.bc2_list)}

        self.umi_base_length = umi_base_length
        self.offsets = tuple(offsets)
        self.split_order = tuple(split_order)
        self.hd_bins = hd_bins

        print(
            f"Visium HD exact matching enabled. "
            f"BC1={len(self.bc1_list)} whitelist entries, "
            f"BC2={len(self.bc2_list)} whitelist entries, "
            f"offsets={self.offsets}, base UMI length={self.umi_base_length}."
        )
    
    # function to annotate reads (read starts directly after truseq)
    def decode(self, sequence):
        # length check
        min_required = self.umi_base_length + min(self.offsets) + min(l1 + l2 for l1, l2 in self.split_order)
        if len(sequence) < min_required:
            return None
        # start with umi=9 base and look for spbc matches with offset 0,1,2
        for offset in self.offsets:
            umi_len = self.umi_base_length + offset

            if len(sequence) < umi_len:
                continue

            umi = sequence[:umi_len]
            bc_start = umi_len
            # 
            for l1, l2 in self.split_order:
                total_needed = umi_len + l1 + l2
                if len(sequence) < total_needed:
                    continue

                bc1 = sequence[bc_start:bc_start + l1]
                bc2 = sequence[bc_start + l1:bc_start + l1 + l2]
                # exact check against whitelists
                if bc1 in self.bc1_set_by_len.get(l1, set()) and bc2 in self.bc2_set_by_len.get(l2, set()):
                    spbc = bc1 + bc2
                    x = self.bc1_index[bc1]
                    y = self.bc2_index[bc2]
                    spbc10x = f"s_{self.hd_bins}_{x:05d}_{y:05d}-1"

                    trim_len = umi_len + l1 + l2
                    # info for new header
                    return {
                        "mode": "visiumhd",
                        "trim_len": trim_len,
                        "header_fields": [
                            f"UMI={umi}",
                            f"BC1={bc1}",
                            f"BC2={bc2}",
                            f"SPBC={spbc}",
                            f"UMISPBC={umi}{spbc}",
                            f"X={x}",
                            f"Y={y}",
                            f"SPBC10X={spbc10x}",
                        ],
                    }

        return None


# ----------------------------
# Shared processing loop
# ----------------------------
# main function, read-in, decoding, cut off annotated segment and output
def annotate_spatial_reads(input_fasta, output_fasta, decoder, failed_fasta=None, cut=True):
    cut = parse_bool(cut)
    # for logging
    total_sequences = 0
    retained_sequences = 0
    filtered_out_sequences = 0
    too_short_sequences = 0
    # failed reads
    failed_handle = open(failed_fasta, "w") if failed_fasta else None

    try:
        with open(output_fasta, "w") as output_handle:
            for record in SeqIO.parse(input_fasta, "fasta"):
                total_sequences += 1
                sequence = str(record.seq)

                result = decoder.decode(sequence)

                if result is None:
                    filtered_out_sequences += 1
                    write_failed_record(record, failed_handle, "Failed barcode/UMI annotation")
                    continue
                
                trim_len = result["trim_len"]
                # build new header
                new_id = f"{record.id}|" + "|".join(result["header_fields"])
                record.id = new_id
                record.description = ""
                # cut reads
                if cut:
                    trimmed_seq = sequence[trim_len:]
                    record.seq = Seq(trimmed_seq)
                # write output
                if len(record.seq) > 0:
                    SeqIO.write(record, output_handle, "fasta")
                    retained_sequences += 1
                else:
                    filtered_out_sequences += 1
                    too_short_sequences += 1
                    write_failed_record(record, failed_handle, "Trimmed sequence length 0")
    # close failed file
    finally:
        if failed_handle:
            failed_handle.close()
    # logging
    print("\n")
    print("Spatial barcode / UMI annotation:")
    print("\n")
    print(f"Total sequences processed: {total_sequences}")
    print(f"Sequences retained: {retained_sequences}")
    print(f"Sequences failed annotation or zero-length after trimming: {filtered_out_sequences}")
    print(f"Zero-length after trimming: {too_short_sequences}")
    print("\n")


def parse_args():
    parser = argparse.ArgumentParser(description="Process FASTA file to extract SPBC/BC and UMI information.")

    parser.add_argument("-i", "--input", required=True, help="Path to the input FASTA file")
    parser.add_argument("-o", "--output", required=True, help="Path to the output FASTA file")
    parser.add_argument("--failed", help="Path to the output FASTA file for failed sequences")
    parser.add_argument("--cut", type=str, default="True", help="Specify whether to cut annotated segments from sequence (default: True)")
    parser.add_argument("--spatial_mode", choices=["visium", "visiumhd"], default="visium", help="Spatial barcode mode (default: visium)")

    # Visium arguments
    parser.add_argument("--spbc_file", help="Path to valid SPBC whitelist file (Visium mode)")
    parser.add_argument("--spbc_length", type=int, default=16, help="Length of the SPBC sequence in Visium mode (default: 16)")
    parser.add_argument("--umi_length", type=int, default=12, help="Length of the UMI sequence in Visium mode (default: 12)")
    parser.add_argument("--mismatch_fraction", type=float, default=0.0, help="Fraction of allowed mismatches between SPBCs in Visium mode (default: 0.0)")

    # Visium HD arguments
    parser.add_argument("--bc1_file", help="Path to valid BC1 whitelist file (Visium HD mode)")
    parser.add_argument("--bc2_file", help="Path to valid BC2 whitelist file (Visium HD mode)")
    parser.add_argument("--hd_umi_base_length", type=int, default=9, help="Base UMI length for Visium HD mode before offset nt are included (default: 9)")
    parser.add_argument("--hd_offsets", type=str, default="0,1,2", help="Comma-separated offsets to try in Visium HD mode (default: 0,1,2)")
    parser.add_argument("--hd_bins", type=str, default="002um", help="Prefix used in SPBC10X barcode for Visium HD mode (default: 002um)")

    return parser.parse_args()


def main():
    args = parse_args()

    if args.spatial_mode == "visium":
        if args.spbc_file is None:
            raise ValueError("--spbc_file is required in --spatial_mode visium")
        if args.mismatch_fraction < 0.0:
            raise ValueError("--mismatch_fraction must be >= 0.0")

        decoder = VisiumDecoder(
            spbc_file=args.spbc_file,
            spbc_length=args.spbc_length,
            umi_length=args.umi_length,
            mismatch_fraction=args.mismatch_fraction,
        )

    elif args.spatial_mode == "visiumhd":
        if args.bc1_file is None or args.bc2_file is None:
            raise ValueError("--bc1_file and --bc2_file are required in --spatial_mode visiumhd")

        try:
            offsets = tuple(int(x) for x in args.hd_offsets.split(",") if x.strip() != "")
        except ValueError:
            raise ValueError("--hd_offsets must be a comma-separated list of integers, e.g. 0,1,2")

        decoder = VisiumHDDecoder(
            bc1_file=args.bc1_file,
            bc2_file=args.bc2_file,
            umi_base_length=args.hd_umi_base_length,
            offsets=offsets,
            hd_bins=args.hd_bins,
        )

    else:
        raise ValueError(f"Unsupported spatial mode: {args.spatial_mode}")

    annotate_spatial_reads(
        input_fasta=args.input,
        output_fasta=args.output,
        decoder=decoder,
        failed_fasta=args.failed,
        cut=args.cut,
    )


if __name__ == "__main__":
    main()
