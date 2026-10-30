"""
Build the EUFP Corpus (v1) from the scraped text files.

EUFP Corpus: EU Foreign Policy Institutional Communication, 2015-2025
Author: Sasha Juul Nielsen, Department of Global Studies, Aarhus University
Corpus DOI: https://doi.org/10.5281/zenodo.23806268
Licence: MIT (see LICENSE)

Input
-----
One folder per institution, as produced by the scraping code:

    <INPUT_FOLDER>/
        EC Data/      urls.txt   EC Texts/document_1.txt, document_2.txt, ...
        FAC Data/     urls.txt   FAC Texts/...
        HR Data/      urls.txt   HR Texts/...
        EEAS Data/    urls.txt   EEAS Texts/...
        EComm Data/   urls.txt   EComm Texts/...

document_N.txt is the page at line N of urls.txt. Each file has the form

    <date text> - <title>
    <empty line>
    <body text>

Output
------
eufp_corpus_v1.parquet and eufp_corpus_v1.csv (UTF-8 with byte-order mark),
one row per document, 18 columns. See README.md for a description of all
columns, flags and decisions.

Requirements: Python 3.9+, pandas, pyarrow, langdetect (see requirements.txt)

Usage: set INPUT_FOLDER and OUTPUT_FOLDER below, then run
    python build_eufp_corpus.py
"""

import hashlib
import os
import re
from datetime import datetime

import pandas as pd
from langdetect import DetectorFactory, LangDetectException, detect

# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------

INPUT_FOLDER = r"path/to/scraped/data"        # folder holding the five "<INST> Data" folders
OUTPUT_FOLDER = r"eufp_corpus_output"          # where the corpus files are written
OUTPUT_NAME = "eufp_corpus_v1"

INSTITUTIONS = ["EC", "FAC", "HR", "EEAS", "EComm"]
START, END = pd.Timestamp("2015-01-01"), pd.Timestamp("2025-12-31")

SHORT_TEXT_WORDS = 20      # short_text: fewer than this many words
LONG_TEXT_WORDS = 5000     # long_text: more than this many words
LANGUAGE_CHARS = 3000      # characters used for language detection

# Documents whose text does not correspond to their title (identified by
# manual review: the scraper captured an attached PDF instead of the page).
SUSPECT_TEXT = [
    "FAC_000023", "FAC_000024", "FAC_000078", "FAC_000082", "FAC_000089",
    "FAC_000334", "FAC_000341", "EC_000332", "EC_000368",
]

# Document type: EComm from the reference code in the URL ...
ECOMM_TYPES = {"ip": "press release", "speech": "speech", "statement": "statement"}

# ... other institutions from keywords in the title (first match wins).
TITLE_RULES = [
    ("joint statement", "joint statement"),
    ("declaration", "declaration"),
    ("statement", "statement"),
    ("remarks", "remarks"),
    ("press conference", "remarks"),
    ("speech", "speech"),
    ("address", "speech"),
    ("intervention", "speech"),
    ("conclusions", "conclusions"),
    ("indicative programme", "agenda"),
    ("agenda", "agenda"),
    ("media advisory", "media advisory"),
    ("main results", "meeting results"),
    ("factsheet", "factsheet"),
    ("fact sheet", "factsheet"),
    ("letter", "letter"),
    ("interview", "interview"),
    ("op-ed", "op-ed / blog"),
    ("blog", "op-ed / blog"),
]

FINAL_COLUMNS = [
    "doc_id", "institution", "date", "time", "title", "doc_type", "language",
    "word_count", "short_text", "long_text", "suspect_text",
    "duplicate_group", "also_in", "match",
    "url", "scrape_date", "source_file", "text",
]


# ----------------------------------------------------------------------------
# Step 1: Read files, URLs and scrape dates
# ----------------------------------------------------------------------------

def read_institution(inst):
    folder = os.path.join(INPUT_FOLDER, f"{inst} Data")
    text_folder = os.path.join(folder, f"{inst} Texts")
    with open(os.path.join(folder, "urls.txt"), encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    rows, missing = [], 0
    for n, url in enumerate(urls, start=1):
        path = os.path.join(text_folder, f"document_{n}.txt")
        if not os.path.exists(path):
            missing += 1
            continue
        with open(path, encoding="utf-8", errors="replace") as f:
            raw_text = f.read()
        rows.append({
            "institution": inst,
            "file_number": n,
            "url": url,
            "scrape_date": datetime.fromtimestamp(os.path.getmtime(path)).date(),
            "raw_text": raw_text,
        })
    print(f"  {inst}: {len(rows):,} files read, {missing} URLs without a file")
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Step 2: Split header and body; parse dates and times
# ----------------------------------------------------------------------------

def split_document(raw_text):
    header, _, body = raw_text.partition("\n")
    # The date text ends at the first " - " (or a final " -" when the title
    # is empty). A dash without a following space, as in "SURINAME -DUTCH",
    # belongs to the date text (e.g. an EEAS delegation name).
    parts = re.split(r" -(?: |$)", header, maxsplit=1)
    date_text = parts[0]
    title = parts[1] if len(parts) > 1 else ""
    return date_text.strip(), title.strip(), body.strip()


def parse_date(inst, date_text):
    try:
        if inst in ("EC", "FAC", "HR"):
            dt = datetime.strptime(date_text, "%d %B %Y %H:%M")
            return dt.date(), dt.strftime("%H:%M")
        if inst == "EEAS":
            return datetime.strptime(date_text.split()[0], "%d.%m.%Y").date(), None
        if inst == "EComm":
            return datetime.strptime(date_text, "%b %d, %Y").date(), None
    except (ValueError, IndexError):
        pass
    return None, None


# ----------------------------------------------------------------------------
# Step 3: Derived columns
# ----------------------------------------------------------------------------

def doc_type(inst, title, url):
    if inst == "EComm":
        code = url.rstrip("/").rsplit("/", 1)[-1].split("_")[0]
        return ECOMM_TYPES.get(code, "other")
    t = title.lower()
    for keyword, label in TITLE_RULES:
        if keyword in t:
            return label
    return "press release / other"


def main_language(text):
    try:
        return detect(text[:LANGUAGE_CHARS])
    except LangDetectException:
        return "unknown"


# ----------------------------------------------------------------------------
# Step 4: Duplicate groups
# ----------------------------------------------------------------------------

def fingerprint(text):
    tidy = " ".join(text.lower().split())
    return hashlib.md5(tidy.encode("utf-8")).hexdigest()


def add_duplicate_columns(corpus):
    corpus["url_clean"] = corpus["url"].str.lower().str.rstrip("/")
    corpus["text_fp"] = corpus["text"].apply(fingerprint)
    corpus.loc[corpus["short_text"], "text_fp"] = None   # not compared

    url_dup = corpus.duplicated("url_clean", keep=False)
    text_dup = corpus["text_fp"].notna() & corpus.duplicated("text_fp", keep=False)

    # Link all documents that share a URL or a text (union-find)
    parent = {d: d for d in corpus["doc_id"]}

    def find(d):
        while parent[d] != d:
            parent[d] = parent[parent[d]]
            d = parent[d]
        return d

    for column, mask in [("url_clean", url_dup), ("text_fp", text_dup)]:
        for _, group in corpus[mask].groupby(column):
            ids = list(group["doc_id"])
            for other in ids[1:]:
                parent[find(other)] = find(ids[0])

    corpus["root"] = corpus["doc_id"].map(find)
    in_group = corpus.groupby("root")["doc_id"].transform("size") > 1

    # Number groups 1, 2, 3, ... in corpus order
    roots = corpus.loc[in_group, "root"].drop_duplicates()
    numbers = {r: i for i, r in enumerate(roots, start=1)}
    corpus["duplicate_group"] = corpus["root"].map(numbers).astype("Int64")

    # also_in: institutions of the other copies
    corpus["also_in"] = None
    for _, group in corpus[in_group].groupby("root"):
        for idx in group.index:
            others = group.drop(idx)["institution"]
            corpus.at[idx, "also_in"] = "; ".join(sorted(set(others)))

    # match: how the copies were found
    corpus["match"] = None
    corpus.loc[url_dup & ~text_dup, "match"] = "url"
    corpus.loc[~url_dup & text_dup, "match"] = "text"
    corpus.loc[url_dup & text_dup, "match"] = "url + text"
    corpus.loc[in_group & corpus["match"].isna(), "match"] = "linked via another copy"

    print(f"  {in_group.sum():,} documents in {len(numbers):,} duplicate groups")
    return corpus


# ----------------------------------------------------------------------------
# Build
# ----------------------------------------------------------------------------

def build():
    print("Step 1: reading files")
    raw = pd.concat([read_institution(i) for i in INSTITUTIONS], ignore_index=True)

    print("Step 2: splitting headers and parsing dates")
    raw[["date_text", "title", "body"]] = raw["raw_text"].apply(
        lambda t: pd.Series(split_document(t)))
    raw[["date", "time"]] = raw.apply(
        lambda r: pd.Series(parse_date(r["institution"], r["date_text"])), axis=1)
    raw["date"] = pd.to_datetime(raw["date"])
    unreadable = raw["date"].isna().sum()
    if unreadable:
        print(f"  WARNING: {unreadable} documents with an unreadable date")

    corpus = raw[(raw["date"] >= START) & (raw["date"] <= END)].copy()
    corpus.loc[corpus["time"] == "00:00", "time"] = None   # 00:00 = no time given
    print(f"  {len(corpus):,} documents dated {START.date()} to {END.date()}")

    print("Step 3: IDs, document types, languages, word counts, flags")
    corpus = corpus.sort_values(
        ["institution", "date", "time", "file_number"],
        ascending=[True, True, True, False], na_position="first")
    corpus["doc_id"] = (corpus["institution"] + "_" +
        (corpus.groupby("institution").cumcount() + 1).astype(str).str.zfill(6))
    corpus["doc_type"] = corpus.apply(
        lambda r: doc_type(r["institution"], r["title"], r["url"]), axis=1)

    print("  detecting languages (this takes several minutes)")
    DetectorFactory.seed = 0
    corpus["language"] = corpus["body"].apply(main_language)

    corpus["word_count"] = corpus["body"].str.split().str.len()
    corpus["short_text"] = corpus["word_count"] < SHORT_TEXT_WORDS
    corpus["long_text"] = corpus["word_count"] > LONG_TEXT_WORDS
    corpus["suspect_text"] = corpus["doc_id"].isin(SUSPECT_TEXT)
    corpus["source_file"] = "document_" + corpus["file_number"].astype(str) + ".txt"
    corpus["date"] = corpus["date"].dt.date
    corpus = corpus.rename(columns={"body": "text"}).reset_index(drop=True)

    print("Step 4: duplicate groups")
    corpus = add_duplicate_columns(corpus)

    return corpus[FINAL_COLUMNS]


def save(corpus):
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    parquet_path = os.path.join(OUTPUT_FOLDER, OUTPUT_NAME + ".parquet")
    csv_path = os.path.join(OUTPUT_FOLDER, OUTPUT_NAME + ".csv")
    corpus.to_parquet(parquet_path, index=False)
    corpus.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"Saved {len(corpus):,} documents to {OUTPUT_FOLDER}")


if __name__ == "__main__":
    corpus = build()
    save(corpus)
