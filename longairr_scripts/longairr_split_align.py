#!/usr/bin/env python3

import argparse
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from Bio import SeqIO
import math

#================================================================#
#
#        Script:  longairr_split_align.py
#         Usage:  Internal script used in 'longairr.sh/longairr collapse'
#
#   DESCRIPTION:  Script splits (subsampled) sequence_groups into distinct files.
#                 These 'chunks' are used to evenly distribute sequence_groups
#                 across multiple files to reduce computational load for MSA per
#                 sequence_group. Number of sequence_groups per chunk can be specified (--max_umi_per_chunk).
#                 Sorting logic as follows: Groups with 1-3 reads populate the 
#                 first 3 chunks respectively.
#                 For remaining groups, we first compute a estimated number of chunks to set a soft-limit for 
#                 the number of reads per chunk, with the hard limit set to the
#                 specified number of groups per chunk.
#                 The first group of each chunk is a large group, the chunk is then filled from the other end of the 
#                 sorted list up to the number of specified allowed groups or 
#                 less groups if the soft-limit condition is met.
#
#        AUTHOR:  Jonas Schuck, jschuckdev@gmail.com
#    BUG-REPORT:  https://github.com/AGImkeller/LongAIRR/issues
#
#================================================================#


# Get grouping-sequence from headers
def extract_umi(header, field="SPBCUMI"):
    for token in header.replace('|', ' ').split():
        if token.startswith(f"{field}="):
            return token.split('=')[1]
    return None


# Write chunk to file and reset log-counters for next chunk
def write_chunk(current_chunk, out_dir, chunk_index, chunk_records, chunk_sizes, chunk_umis):

    if not current_chunk['groups']:
        return

    chunk_file = out_dir / f"chunk_{chunk_index:03d}.fasta"
    SeqIO.write(
        [rec for group in current_chunk['groups'] for rec in group],
        chunk_file,
        "fasta"
    )

    # Update chunk info for proper logging
    all_records = [rec for group in current_chunk['groups'] for rec in group]
    chunk_records.append(all_records)
    chunk_sizes.append(current_chunk['size'])
    chunk_umis.append(current_chunk['umis'])
    print(f"Created {chunk_file.name} with {current_chunk['size']} reads, {current_chunk['umis']} groups.")

    # Reset counters for next chunk
    current_chunk['groups'] = []
    current_chunk['size'] = 0
    current_chunk['umis'] = 0


# Split umi_groups into chunks
def split_fasta_by_umi(fasta_file, group_field, max_umi_per_chunk, out_dir):

    print(f"\n\nCreating chunks..")
    print(f"Reading sequences from {fasta_file}...")
    print(f"Grouping by: {group_field}\n")
    umi_groups = defaultdict(list)

    # Get UMI sequences and add them to dictionary
    for record in SeqIO.parse(fasta_file, "fasta"):
        umi = extract_umi(record.description, group_field)
        if umi:
            umi_groups[umi].append(record)
        else:
            print(f"[WARNING] Skipping sequence without {group_field}: {record.id}")

    print(f"Found {len(umi_groups)} unique groups.\n")

    # Separate the groups based on their read counts (1, 2, 3, and then >=4)
    groups_by_size = {1: [], 2: [], 3: [], 'remaining': []}
    for group in umi_groups.values():
        if len(group) == 1:  # Singles
            groups_by_size[1].append(group)
        elif len(group) == 2:  # Doubles
            groups_by_size[2].append(group)
        elif len(group) == 3:  # Triples
            groups_by_size[3].append(group)
        else:  # All reads with larger umi_group size
            groups_by_size['remaining'].append(group)

    chunk_records = []
    chunk_sizes = []
    chunk_umis = []

    # Write chunk files for singles, doubles, triples into chunk_001-003
    for idx, group_type in enumerate([1, 2, 3], start=1):
        groups = groups_by_size[group_type]
        if groups:
            chunk_file = out_dir / f"chunk_{idx:03d}.fasta"
            all_records = [rec for group in groups for rec in group]
            SeqIO.write(all_records, chunk_file, "fasta")
            chunk_records.append(all_records)
            chunk_sizes.append(len(all_records))
            chunk_umis.append(len(groups))
            print(f"Created {chunk_file.name} with {len(all_records)} reads.")

    # Process the remaining sequence_groups (size >= 4)
    remaining_groups = groups_by_size['remaining']

    if not remaining_groups:
        # No remaining groups; just write chunk_info and return
        info_path = out_dir / "chunks_info.tsv"
        with open(info_path, "w") as mf:
            mf.write("chunk_filename\tnum_reads\tnum_groups\n")
            for i, (chunk, chunk_size, chunk_umi_count) in enumerate(zip(chunk_records, chunk_sizes, chunk_umis)):
                chunk_file = out_dir / f"chunk_{i+1:03d}.fasta"
                mf.write(f"{chunk_file.name}\t{chunk_size}\t{chunk_umi_count}\n")
        return out_dir

    # Build (size, group) tuples and sort by size descending
    sized_groups = [(len(g), g) for g in remaining_groups]
    sized_groups.sort(key=lambda x: x[0], reverse=True)

    num_remaining_umis = len(sized_groups)
    total_remaining_reads = sum(size for size, _ in sized_groups)

    # Estimate how many chunks we will need for the remaining groups
    # to compute soft_limit to evenly distribute reads and number of groups across chunks
    num_chunks_est = max(1, math.ceil(num_remaining_umis / max_umi_per_chunk))
    target_reads_per_chunk = total_remaining_reads / num_chunks_est
    soft_limit = target_reads_per_chunk * 1.25  # allow some slack

    # Track which groups have been used
    used = [False] * len(sized_groups)

    chunk_index = 4

    # Main chunking loop for remaining groups
    while True:
        # Find next largest unused group (start of new chunk)
        start_idx = None
        for i, (size, group) in enumerate(sized_groups):
            if not used[i]:
                start_idx = i
                break

        if start_idx is None:
            break  # no more groups

        # Start a new chunk with this largest unused group
        start_size, start_group = sized_groups[start_idx]
        used[start_idx] = True

        current_groups = [start_group]
        current_reads = start_size
        current_umis = 1

        # Fill with smallest unused groups, as long as we stay within limits
        right = len(sized_groups) - 1
        while current_umis < max_umi_per_chunk:
            # find next unused group from the end (smallest sizes)
            while right >= 0 and used[right]:
                right -= 1
            if right < 0:
                break

            cand_size, cand_group = sized_groups[right]

            # Try to keep total reads per chunk around soft_limit, but allow overshoot if needed
            if current_reads + cand_size <= soft_limit or current_umis == 0:
                used[right] = True
                current_groups.append(cand_group)
                current_reads += cand_size
                current_umis += 1
                right -= 1
            else:
                # This candidate would overshoot too much; try the next smaller one
                right -= 1
                # If we run out of candidates, we stop filling
                if right < 0:
                    break

        # Write this chunk
        current_chunk = {'groups': current_groups, 'size': current_reads, 'umis': current_umis}
        write_chunk(current_chunk, out_dir, chunk_index, chunk_records, chunk_sizes, chunk_umis)
        chunk_index += 1

    # Create chunk_info with chunk logs
    info_path = out_dir / "chunks_info.tsv"
    with open(info_path, "w") as mf:
        mf.write("chunk_filename\tnum_reads\tnum_groups\n")
        for i, (chunk, chunk_size, chunk_umi_count) in enumerate(zip(chunk_records, chunk_sizes, chunk_umis)):
            chunk_file = out_dir / f"chunk_{i+1:03d}.fasta"
            mf.write(f"{chunk_file.name}\t{chunk_size}\t{chunk_umi_count}\n")

    return out_dir


def parse_args():
    parser = argparse.ArgumentParser(description="Split FASTA by UMI groups into chunks")
    parser.add_argument("fasta", help="Input FASTA file")
    parser.add_argument("-g", "--group-field", required=True, default="SPBCUMI", help="Header slot to group sequences by, default 'SPBCUMI'")
    parser.add_argument("--max_umi_per_chunk", type=int, default=32, help="Target number of UMI groups per chunk (default: 32)")
    parser.add_argument("--outdir", default=None, help="Optional output directory (default: auto-generated)")
    return parser.parse_args()


def main():
    args = parse_args()

    # Create the output directory if it does not exist
    out_dir = Path(args.outdir) if args.outdir else Path(f"chunks_{Path(args.fasta).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    out_dir.mkdir(exist_ok=True)

    chunk_dir = split_fasta_by_umi(
        fasta_file=args.fasta,
        group_field=args.group_field,
        max_umi_per_chunk=args.max_umi_per_chunk,
        out_dir=out_dir
    )

    print(f"\nFinished creating chunks. Output in: {chunk_dir}\n")


if __name__ == "__main__":
    main()
