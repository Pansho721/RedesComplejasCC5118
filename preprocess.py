import collections
import csv
import sys
import os

def tsv2file(input, output, sep='\t', head=10, cols=None, count=False):
    os.makedirs(os.path.dirname(output), exist_ok=True) if os.path.dirname(output) else None
    with open(input, newline='', encoding='utf-8') as f:
        with open(output, "w", newline="", encoding="utf-8") as out_f:
            writer = csv.writer(out_f, delimiter='\t')
            # try to sniff delimiter if sep is 'auto'
            if sep == 'auto':
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters='\t,; ')
                    sep_used = dialect.delimiter
                except Exception:
                    sep_used = '\t'
            else:
                sep_used = sep

            reader = csv.reader(f, delimiter=sep_used)
            try:
                header = next(reader)
            except StopIteration:
                print("empty file", file=sys.stderr)
                return

            if cols:
                idxs = []
                for c in cols:
                    try:
                        idxs.append(header.index(c))
                    except ValueError:
                        print(f"column not found: {c}", file=sys.stderr)
                        return
            else:
                idxs = None

            print("Delimiter:", repr(sep_used))
            print("Header:", header if not idxs else [header[i] for i in idxs])

            total = 0
            out_rows = []
            
            # if head==0, process all data rows and count
            for row in reader:
                total += 1
                if idxs:
                    row = [row[i] if i < len(row) else '' for i in idxs]
                if len(row) >= 2:
                        src = row[0].strip()
                        dst = row[1].strip()
                        w = row[2].strip() if len(row) >= 3 else ''
                        if src and dst and w:
                            out_rows.append([src, dst, w])
                        elif src and dst:
                            out_rows.append([src, dst])

            # Sort output rows deterministically by source, target, and optional weight.
            out_rows.sort(key=lambda r: (r[0], r[1], r[2] if len(r) >= 3 else ''))
            writer.writerows(out_rows)

            if count:
                print("Total rows (excluding header):", total)



def directedSimpleGraphFile(input_path, output_path="graphs/graph.edgelist", sep='\t'):
    tsv2file(
        input_path,
        output=output_path,
        sep=sep,
        head=0,
        cols=["SOURCE_SUBREDDIT", "TARGET_SUBREDDIT"],
        count=True,
    )

def directedWeightedGraphFile(input_path, output_path="graphs/graph.edgelist", sep='\t'):
    tsv2file(
        input_path,
        output=output_path,
        sep=sep,
        head=0,
        cols=("SOURCE_SUBREDDIT", "TARGET_SUBREDDIT", "LINK_SENTIMENT"),
        count=True,
    )


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

def filterSentiment(input_path="graphs/reddit_weighted_aggregated.edgelist", outputPos="graphs/reddit_positive.edgelist", outputNeg="graphs/reddit_negative.edgelist", sep='\t'):
    with open(input_path, 'r', encoding='utf-8') as inf, open(outputPos, 'w', newline='', encoding='utf-8') as outfPos, open(outputNeg, 'w', newline='', encoding='utf-8') as outfNeg:
        reader = csv.reader(inf, delimiter=sep)
        writerPos = csv.writer(outfPos, delimiter=sep)
        writerNeg = csv.writer(outfNeg, delimiter=sep)
        for row in reader:
            if len(row) >= 4:
                src, dst, sent, count = row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip()
                try:
                    count = int(count)
                except ValueError:
                    continue
                if sent == '1' and count > 0:
                    writerPos.writerow([src, dst, count])
                elif sent == '-1' and count > 0:
                    writerNeg.writerow([src, dst, count])

if __name__ == "__main__":
    input_file = "soc-redditHyperlinks-body.tsv"
    directedSimpleGraphFile(input_file, "graphs/reddit.edgelist")
    directedWeightedGraphFile(input_file, "graphs/reddit_weighted.edgelist")
    map_reduce_count_edges("graphs/reddit_weighted.edgelist", "graphs/reddit_weighted_aggregated.edgelist", sep='\t')
    filterSentiment("graphs/reddit_weighted_aggregated.edgelist", "graphs/reddit_positive.edgelist", sep='\t')
