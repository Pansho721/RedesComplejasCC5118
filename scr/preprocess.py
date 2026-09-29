"""Stage 1: turn the raw SNAP Reddit-Hyperlinks TSV into the edgelists every
later stage reads. Ported from the old root-level preprocess.py - the row
parsing logic is unchanged, only paths and the entry point moved.

This module has no __main__ block: it is a library called by scr/main.py,
which owns all the tunable paths (see CONFIG in main.py).
"""
import collections
import csv
import os

REQUIRED_COLUMNS = ("SOURCE_SUBREDDIT", "TARGET_SUBREDDIT", "LINK_SENTIMENT")


def validate_input(path, required_columns=REQUIRED_COLUMNS):
    """Sanity-check that `path` looks like the expected dataset before the
    pipeline spends minutes parsing it. Raises on failure."""
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Input dataset not found: {path}\n"
            "Download 'soc-redditHyperlinks-body.tsv' from "
            "https://snap.stanford.edu/data/soc-RedditHyperlinks.html and place it there."
        )
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
    missing = [c for c in required_columns if c not in header]
    if missing:
        raise ValueError(f"Input dataset {path} is missing expected column(s): {missing}")
    return True


def tsv2file(input, output, sep="\t", head=10, cols=None, count=False):
    os.makedirs(os.path.dirname(output), exist_ok=True) if os.path.dirname(output) else None
    with open(input, newline="", encoding="utf-8") as f:
        with open(output, "w", newline="", encoding="utf-8") as out_f:
            writer = csv.writer(out_f, delimiter="\t")
            if sep == "auto":
                sample = f.read(4096)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters="\t,; ")
                    sep_used = dialect.delimiter
                except Exception:
                    sep_used = "\t"
            else:
                sep_used = sep

            reader = csv.reader(f, delimiter=sep_used)
            try:
                header = next(reader)
            except StopIteration:
                print("empty file")
                return

            if cols:
                idxs = []
                for c in cols:
                    try:
                        idxs.append(header.index(c))
                    except ValueError:
                        print(f"column not found: {c}")
                        return
            else:
                idxs = None

            print("Delimiter:", repr(sep_used))
            print("Header:", header if not idxs else [header[i] for i in idxs])

            total = 0
            out_rows = []

            for row in reader:
                total += 1
                if idxs:
                    row = [row[i] if i < len(row) else "" for i in idxs]
                if len(row) >= 2:
                    src = row[0].strip()
                    dst = row[1].strip()
                    w = row[2].strip() if len(row) >= 3 else ""
                    if src and dst and w:
                        out_rows.append([src, dst, w])
                    elif src and dst:
                        out_rows.append([src, dst])

            # Sort output rows deterministically by source, target, and optional weight.
            out_rows.sort(key=lambda r: (r[0], r[1], r[2] if len(r) >= 3 else ""))
            writer.writerows(out_rows)

            if count:
                print("Total rows (excluding header):", total)


def directedSimpleGraphFile(input_path, output_path):
    tsv2file(
        input_path,
        output=output_path,
        sep="\t",
        head=0,
        cols=["SOURCE_SUBREDDIT", "TARGET_SUBREDDIT"],
        count=True,
    )


def directedWeightedGraphFile(input_path, output_path):
    tsv2file(
        input_path,
        output=output_path,
        sep="\t",
        head=0,
        cols=("SOURCE_SUBREDDIT", "TARGET_SUBREDDIT", "LINK_SENTIMENT"),
        count=True,
    )


def map_reduce_count_edges(input_path, output_path, sep="\t"):
    counter = collections.Counter()
    with open(input_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.rstrip("\n")
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

    with open(output_path, "w", newline="", encoding="utf-8") as outf:
        writer = csv.writer(outf, delimiter=sep)
        for (src, dst, sent), cnt in counter.items():
            writer.writerow([src, dst, sent, cnt])

    return output_path


def filterSentiment(input_path, outputPos, outputNeg, sep="\t"):
    with open(input_path, "r", encoding="utf-8") as inf, \
         open(outputPos, "w", newline="", encoding="utf-8") as outfPos, \
         open(outputNeg, "w", newline="", encoding="utf-8") as outfNeg:

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
                if sent == "1" and count > 0:
                    writerPos.writerow([src, dst, count])
                elif sent == "-1" and count > 0:
                    writerNeg.writerow([src, dst, count])


# [src, dst, neg_count, pos_count, total, pos_proportion, neg_proportion]
def makeSummary(pos_file, neg_file, summary_file, sep="\t"):
    summary = {}
    with open(pos_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=sep)
        for row in reader:
            if len(row) >= 3:
                src, dst, count = row[0].strip(), row[1].strip(), row[2].strip()
                try:
                    count = int(count)
                except ValueError:
                    count = 0
                summary[(src, dst)] = [0, count]  # [neg_count, pos_count]
    with open(neg_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=sep)
        for row in reader:
            if len(row) >= 3:
                src, dst, count = row[0].strip(), row[1].strip(), row[2].strip()
                try:
                    count = int(count)
                except ValueError:
                    count = 0
                if (src, dst) in summary:
                    summary[(src, dst)][0] = count
                else:
                    summary[(src, dst)] = [count, 0]
    with open(summary_file, "w", encoding="utf-8") as outf:
        writer = csv.writer(outf, delimiter=sep)
        for (src, dst), (neg_count, pos_count) in summary.items():
            total = neg_count + pos_count
            if total < 0:
                continue
            writer.writerow([src, dst, neg_count, pos_count, total, pos_count / total, neg_count / total])


def run(config):
    """Entry point called by scr/main.py. Returns a dict of the edgelist
    paths produced, so later stages don't have to guess filenames."""
    paths = config["paths"]
    input_tsv = paths["input_tsv"]
    edgelist_dir = paths["edgelist_dir"]
    os.makedirs(edgelist_dir, exist_ok=True)

    validate_input(input_tsv)

    out = {
        "simple": os.path.join(edgelist_dir, "reddit.edgelist"),
        "weighted": os.path.join(edgelist_dir, "reddit_weighted.edgelist"),
        "aggregated": os.path.join(edgelist_dir, "reddit_weighted_aggregated.edgelist"),
        "positive": os.path.join(edgelist_dir, "reddit_positive.edgelist"),
        "negative": os.path.join(edgelist_dir, "reddit_negative.edgelist"),
        "summary": os.path.join(edgelist_dir, "reddit_summary.txt"),
    }

    directedSimpleGraphFile(input_tsv, out["simple"])
    directedWeightedGraphFile(input_tsv, out["weighted"])
    map_reduce_count_edges(out["weighted"], out["aggregated"], sep="\t")
    filterSentiment(out["aggregated"], out["positive"], out["negative"], sep="\t")
    makeSummary(out["positive"], out["negative"], out["summary"], sep="\t")

    return out
