import read as rd
import csv
import collections


def write_publishes_edgelist(input_path, output_path="publishes.edgelist", sep='\t', cols=("SOURCE_SUBREDDIT", "TARGET_SUBREDDIT", "LINK_SENTIMENT"), skip_header=True, default_weight=1):
    """Write an edge list file that preserves duplicate publishes.

    Each input row yields one output line. If LINK_SENTIMENT is present it
    is written as the third column; otherwise `default_weight` is used.
    """
    written = 0
    with open(output_path, 'w', newline='', encoding='utf-8') as out_f:
        writer = csv.writer(out_f, delimiter='\t')
        for src, dst, link_sent in rd.iter_reddit_publishes(input_path, sep=sep, cols=cols, skip_header=skip_header):
            if link_sent is None:
                w = default_weight
            else:
                w = link_sent
            writer.writerow([src, dst, w])
            written += 1

    print(f"Wrote {written} rows to {output_path}")
    return output_path


def map_reduce_count_edges(input_path, output_path="aggregated.edgelist", sep='\t', use_external_sort=True):
    """Aggregate (src,dst,sentiment) triples into counts using memory.

    Produces an output file where each line is:
        src <tab> dst <tab> sentiment <tab> count

    The use_external_sort argument is kept for compatibility but ignored.
    """
    counter = collections.Counter()
    with open(input_path, 'r', encoding='utf-8') as inf:
        for line in inf:
            line = line.rstrip('\n')
            if not line:
                continue
            parts = line.split(sep)
            if len(parts) >= 3:
                src, dst, sent = parts[0].strip(), parts[1].strip(), parts[2].strip()
            elif len(parts) == 2:
                src, dst, sent = parts[0].strip(), parts[1].strip(), ''
            else:
                continue
            counter[(src, dst, sent)] += 1

    with open(output_path, 'w', newline='', encoding='utf-8') as outf:
        writer = csv.writer(outf, delimiter=sep)
        for (src, dst, sent), cnt in counter.items():
            writer.writerow([src, dst, sent, cnt])

    return output_path

if __name__ == "__main__":
    out = write_publishes_edgelist("soc-redditHyperlinks-body.tsv", sep='\t', cols=("SOURCE_SUBREDDIT", "TARGET_SUBREDDIT", "LINK_SENTIMENT"), skip_header=True)
    # Aggregate to (src, dst, sentiment, count)
    agg = map_reduce_count_edges(out, output_path='aggregated.edgelist', sep='\t')
    print(f"Aggregated publishes written to: {agg}")
