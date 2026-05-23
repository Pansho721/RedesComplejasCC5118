import collections
import csv
from importlib import simple
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
    counter = collections.Counter()
    with open(input_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.rstrip('\n')
            if not line:
                continue
            parts = line.split(sep)
            if len(parts) >= 3:
                src, dst, sent = parts[0].strip(), parts[1].strip(), parts[2].strip()
            elif len(parts) == 2:
                src, dst, sent = parts[0].strip(), parts[1].strip(), 0
            else:
                continue
            counter[(src, dst, sent)] += 1

    with open(output_path, 'w', newline='', encoding='utf-8') as outf:
        writer = csv.writer(outf, delimiter=sep)
        for (src, dst, sent), cnt in counter.items():
            writer.writerow([src, dst, sent, cnt])

    return output_path

def filterSentiment(input_path="graphs/reddit_weighted_aggregated.edgelist", outputPos="graphs/reddit_positive.edgelist", outputNeg="graphs/reddit_negative.edgelist", sep='\t'):
    with open(input_path, 'r', encoding='utf-8') as inf, \
         open(outputPos,  'w', newline='', encoding='utf-8') as outfPos, \
         open(outputNeg,  'w', newline='', encoding='utf-8') as outfNeg:
        
        reader = csv.reader(inf, delimiter=sep)
        writerPos = csv.writer(outfPos, delimiter=sep)
        writerNeg = csv.writer(outfNeg, delimiter=sep)
        for row in reader:
            if len(row) >= 4:
                src, dst, sent, count = row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip()
                try:
                    count = int(count)
                except ValueError:
                    count = 0
                if sent == '1' and count > 0:
                    writerPos.writerow([src, dst, count])
                elif sent == '-1' and count > 0:
                    writerNeg.writerow([src, dst, count])


# [src, dst, pos_count, neg_count, total_count, pos_proportion, neg_proportion]
def makeSummary(pos_file="graphs/reddit_positive.edgelist", neg_file="graphs/reddit_negative.edgelist", summary_file="graphs/reddit_summary.txt", sep='\t'):
    summary = {}
    with open(pos_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=sep)
        for row in reader:
            if len(row) >= 3:
                src, dst, count = row[0].strip(), row[1].strip(), row[2].strip()
                try:
                    count = int(count)
                except ValueError:
                    count = 0
                summary[(src, dst)] = [0, count]  # [neg_count, pos_count]
    with open(neg_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=sep)
        for row in reader:
            if len(row) >= 3:
                src, dst, count = row[0].strip(), row[1].strip(), row[2].strip()
                try:
                    count = int(count)
                except ValueError:
                    count = 0
                if (src, dst) in summary:
                    summary[(src, dst)][0] = count  # update neg_count
                else:
                    summary[(src, dst)] = [count, 0]  # [neg_count, pos_count]
    with open(summary_file, 'w', encoding='utf-8') as outf:
        writer = csv.writer(outf, delimiter=sep)
        for (src, dst), (neg_count, pos_count) in summary.items():
            sum = neg_count + pos_count
            if sum < 0:
                continue
            writer.writerow([src, dst, neg_count, pos_count, sum, pos_count/sum, neg_count/sum])


if __name__ == "__main__":
    input_file = "soc-redditHyperlinks-body.tsv"
    simple_file = "graphs/reddit.edgelist"
    weight_file = "graphs/reddit_weighted.edgelist"
    aggregated_file = "graphs/reddit_weighted_aggregated.edgelist"
    possitive_file = "graphs/reddit_positive.edgelist"
    negative_file = "graphs/reddit_negative.edgelist"
    summary_file = "graphs/reddit_summary.txt"

    directedSimpleGraphFile(input_file, simple_file)
    directedWeightedGraphFile(input_file, weight_file)
    map_reduce_count_edges(weight_file, aggregated_file, sep='\t')
    filterSentiment(aggregated_file, possitive_file, negative_file, sep='\t')
    makeSummary(possitive_file, negative_file, summary_file, sep='\t')
