#!/usr/bin/env python3

import argparse
import random
from collections import defaultdict

#================================================================#
#
#        Script:  longairr_filter_subsample_groups.py
#         Usage:  Internal script used in 'longairr.sh/longairr collapse'
#
#   DESCRIPTION:  Script that subsamples large umi_groups to a specified size limit.
#                 Subsampling is carried out using a random
#                 seed and from a lexicographically sorted list of reads per
#                 sequence_group to ensure reproducibility.
#
#                 Before subsampling, adaptive filtering is applied. 
#                 Here, reads within each 'sequence group' that have a certain read number
#                 (--min-group-size) are filtered out if their read length does 
#                 not fall within a defined margin around the 
#                 group-specific peak-read-length - i.e. the bin where most read accumulate.
#                 This step removes noise in addition to the fixed-length filtering
#                 done prior to this script (which is performed on all groups / no size limit).
#
#                 Extensive logging information about which
#                 sequence_group is subsampled is generated. The original group size pre filtering
#                 is written to each reads header (N_ORIG slot), in addition, the group size
#                 post-filtering (pre-subsampling) is also written to the header (N_KEEP slot).
#                 Subsampling large sequence_groups extensively reduces 
#                 computational load of downstream MSA processes.
#
#        AUTHOR:  Jonas Schuck, jschuckdev@gmail.com
#    BUG-REPORT:  https://github.com/AGImkeller/LongAIRR/issues
#
#================================================================#


# Extract GROUP from headers and create GROUP-read dictionary
def parse_fasta_by_umi(input_file,
                       group_field="SPBCUMI"):
    umi_groups = defaultdict(list)
    total_reads = 0
    collapse_field=f"{group_field}="
    with open(input_file, 'r') as infile:
        header, sequence = None, ""
        for line in infile:
            line = line.strip()
            if line.startswith(">"):
                # Add group + (header, sequence) tuple to dictionary
                if header and umi:
                    umi_groups[umi].append((header, sequence))
                    total_reads += 1
                header = line
                sequence = ""
                # Extract GROUP from header
                umi = next((x.split("=")[1] for x in header.split("|") if x.startswith(collapse_field)), None)
            else:
                sequence += line
        # Add last read
        if header and umi:
            umi_groups[umi].append((header, sequence))
            total_reads += 1
    return umi_groups, total_reads


# Perform peak-based adaptive filtering on a sequence_group
def adaptive_filter_group(reads,
                          bin_size=75,
                          rel_margin=0.10):
    if not reads:
        return [], [], {'peak_center': None, 'keep_min': None, 'keep_max': None}

    # Compute read lengths
    lengths = [len(seq) for _, seq in reads]

    # Bin lengths
    bins = {}
    for l in lengths:
        bin_start = (l // bin_size) * bin_size
        bins[bin_start] = bins.get(bin_start, 0) + 1

    # Find peak bin
    peak_bin_start = max(bins, key=lambda k: bins[k])
    peak_center = peak_bin_start + bin_size // 2

    # Compute margin
    margin = rel_margin * peak_center

    keep_min = max(1, int(round(peak_center - margin)))
    keep_max = int(round(peak_center + margin))

    # Filter reads
    kept_reads = []
    failed_reads = []
    for read in reads:
        seq_len = len(read[1])
        if keep_min <= seq_len <= keep_max:
            kept_reads.append(read)
        else:
            failed_reads.append(read)

    stats = {
        'peak_center': peak_center,
        'keep_min': keep_min,
        'keep_max': keep_max,
        'num_filtered': len(failed_reads)
    }

    return kept_reads, failed_reads, stats


# Subsample sequence_groups that are larger than given threshold (using sorted list and random seed)
def subsample_and_write(umi_groups, # input grouped reads
                        output_file, # name of output file
                        group_field="SPBCUMI",
                        max_reads=500, # umi groups with a lower number of seqs wont be subsampled
                        seed=42,
                        total_reads=0, # used for logging, counts input reads
                        adaptive_filter=True, # toggle adaptive filtering
                        filter_threshold=100, # perform adaptive filtering on groups larger (+equal)
                        bin_size=100,
                        rel_margin=0.10,
                        failed_file=None # toggle to write failed-filtered reads into additional output
                        ):
    random.seed(seed)

    # Input-test: anything other than true will become false (also other words)
    if isinstance(adaptive_filter, str):
        adaptive_filter = adaptive_filter.lower() == "true"

    retained_reads = 0

    with open(output_file, 'w') as out:
        failed_reads_combined = []  # to collect all failed reads across sequence groups

        for umi, reads in umi_groups.items():
            n_orig = len(reads)

            # Adaptive filtering for sequence groups starting at specified limit
            if adaptive_filter and n_orig >= filter_threshold:
                kept_reads, failed_reads, stats = adaptive_filter_group(
                    reads, bin_size=bin_size, rel_margin=rel_margin
                )
                n_keep=len(kept_reads) #new count capturing the number of reads before the group is subsampled

                # logging info adaptive filtering
                print(
                    f"{group_field}={umi}, origin size={n_orig}, "
                    f"peak_center={stats['peak_center']}, "
                    f"keep_range={stats['keep_min']}-{stats['keep_max']}, "
                    f"retained={n_keep}, filtered_out={len(failed_reads)}"
                )

                # collect failed reads for combined output
                failed_reads_combined.extend(failed_reads)
            else: # groups that are not filtered
                kept_reads = reads
                n_keep = n_orig

            # Subsample if sequence groups are large (contain more reads than max_reads)
            if len(kept_reads) > max_reads:
                kept_reads = sorted(kept_reads, key=lambda x: (x[0], x[1]))
                sampled_reads = random.sample(kept_reads, max_reads)
                print(f"{group_field}={umi}, origin size={n_orig}, resampled to n={max_reads}")
            else:
                sampled_reads = kept_reads

            # Write sampled reads to output
            seen = set()
            for header, seq in sampled_reads:
                key = (header, seq)
                if key not in seen:
                    header += f"|N_ORIG={n_orig}|N_KEEP={n_keep}"
                    out.write(f"{header}\n{seq}\n")
                    seen.add(key)
                    retained_reads += 1

        print(f"[SUMMARY] Total reads in: {total_reads}  |  Retained after subsampling: {retained_reads}")

    # Write combined failed reads if requested
    if failed_file:
        with open(failed_file, 'w') as ff:
            for header, seq in failed_reads_combined:
                ff.write(f"{header}\n{seq}\n")


def parse_args():
    parser = argparse.ArgumentParser(description="Subsample large UMI groups in a FASTA file.")
    parser.add_argument("-i", "--input", required=True, help="Input FASTA file")
    parser.add_argument("-o", "--output", required=True, help="Output FASTA file")
    parser.add_argument("-n", "--max-reads", type=int, default=500, help="Maximum reads per UMI group (default: 500)")
    parser.add_argument("-f", "--adaptive-filter", type=str, default="True", help="Enable adaptive filtering based on read-length accumulation around a peak (default=True)")
    parser.add_argument("-g", "--group-field",required=True, default="SPBCUMI", help="Header slot to group sequences by, default SPBCUMI")
    parser.add_argument("--min-group-size", type=int, default=5, help="Only apply adaptive filtering to UMI groups with more than this many reads (default: 100)")
    parser.add_argument("--bin-size", type=int, default=100, help="Bin size for read-length histogram used in adaptive filtering (default:100)")
    parser.add_argument("--peak-margin", type=float, default=0.10, help="Relative margin around peak center in adpative filtering (default:0.10)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--failed", help="Optional FASTA file for reads filtered out by adaptive filtering")

    return parser.parse_args()


def main():
    args = parse_args()

    umi_groups, total_reads = parse_fasta_by_umi(args.input,
                                                 group_field=args.group_field)
    subsample_and_write(umi_groups,
                        args.output,
                        group_field=args.group_field,
                        max_reads=args.max_reads,
                        seed=args.seed,
                        total_reads=total_reads,
                        adaptive_filter=args.adaptive_filter,
                        filter_threshold=args.min_group_size,
                        bin_size=args.bin_size,
                        rel_margin=args.peak_margin,
                        failed_file=args.failed)


if __name__ == "__main__":
    main()
