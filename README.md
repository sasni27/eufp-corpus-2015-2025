# EUFP Corpus: EU Foreign Policy Institutional Communication, 2015–2025

**Version:** 1.0
**DOI:** [10.5281/zenodo.23806268](https://doi.org/10.5281/zenodo.23806268)
**Code:** [github.com/sasni27/eufp-corpus-2015-2025](https://github.com/sasni27/eufp-corpus-2015-2025)
**Licence:** CC BY 4.0 (corpus); MIT (code)
**Author:** Sasha Juul Nielsen, Department of Global Studies, Aarhus University
**Contact:** sasni@cas.au.dk
**Release date:** 30 October 2026

---

## 1. Overview

The EUFP Corpus is a collection of **34,634 public communications** (approximately 27.4 million words) issued by five European Union foreign policy institutions between **1 January 2015 and 31 December 2025**: statements, declarations, press releases, remarks, speeches and conclusions.

Each document is provided with its full text, date, title, source URL, document type, language, and a set of flags that make known data-quality issues visible. No document has been removed: dual publications, short and long texts, and other irregularities are retained and recorded in dedicated columns, so that users can decide for themselves what to include.

The corpus was compiled as part of a PhD project at the Department of Global Studies, Aarhus University, and is first used in Nielsen, S.J. (forthcoming). "Decoding diplomacy: A large language model approach to emotional rhetoric across EU foreign policy institutions". For more information, please contact the author (see above).

## 2. Contents

| Institution | Code | Documents | First document | Last document | Source |
|---|---|---:|---|---|---|
| European Council | `EC` | 2,314 | 2015-01-08 | 2025-12-30 | consilium.europa.eu, press releases filtered by entity *European Council* |
| Council of the EU – Foreign Affairs Council | `FAC` | 2,500 | 2015-01-16 | 2025-11-19 | consilium.europa.eu, press releases filtered by Council configuration *Foreign Affairs* |
| High Representative for Foreign Affairs and Security Policy | `HR` | 912 | 2015-01-09 | 2025-12-22 | consilium.europa.eu, press releases filtered by function *High Representative* |
| European External Action Service | `EEAS` | 5,406 | 2015-07-01 | 2025-12-30 | eeas.europa.eu, press material (EEAS) |
| European Commission | `EComm` | 23,502 | 2015-01-02 | 2025-12-31 | ec.europa.eu Press Corner, document types *Press release*, *Speech* and *Statement* |
| **Total** | | **34,634** | | | |

**Note on coverage.** EEAS material begins in July 2015. Pages that could not be downloaded during scraping are not included (EEAS: 9; European Commission: 14).

## 3. Files

| File | Format | Description |
|---|---|---|
| `eufp_corpus_v1.parquet` | Apache Parquet | The full corpus. Recommended for Python and R; preserves column types. |
| `eufp_corpus_v1.csv` | CSV, UTF-8 with byte-order mark | The same data. Opens in Excel and most other software; texts contain line breaks within quoted fields. |
| `eufp_scraped_texts_v1.zip` | ZIP | The scraped source files from which the corpus was built: one text file per collected page (including pages dated 2014, which the build removes) and each institution's list of URLs. Provided for transparency and to allow the corpus to be rebuilt (see Section 5). |
| `README.md` | Markdown | This document. |

One row is one document. The data files are deposited on Zenodo (see DOI above). The GitHub repository contains the build code:

| File (GitHub) | Description |
|---|---|
| `build_eufp_corpus.py` | Builds the corpus from the scraped text files (see Section 5). |
| `requirements.txt` | Python packages needed to run the script. |
| `LICENSE` | MIT licence for the code. |

## 4. Columns

| Column | Type | Description |
|---|---|---|
| `doc_id` | text | Permanent identifier: institution code and a six-digit number, assigned chronologically within each institution (e.g. `FAC_000001`). Use this identifier when citing individual documents. |
| `institution` | text | `EC`, `FAC`, `HR`, `EEAS` or `EComm` (see Section 2). Denotes the website listing under which the document was collected. |
| `date` | date | Publication date as given on the source page. |
| `time` | text (HH:MM) | Publication time, where the source page gives one (EC, FAC and HR only). Empty where unknown. |
| `title` | text | Title as given on the source page. Empty for 373 European Commission documents whose title was not captured; their text is complete. |
| `doc_type` | text | Type of document. For `EComm`, taken from the official reference code in the URL (`ip` = press release, `speech`, `statement`). For the other institutions, derived from keywords in the title (e.g. *declaration*, *remarks*, *conclusions*); titles without a keyword are labelled `press release / other`. For these four institutions, `doc_type` is an approximation, not an official category. |
| `language` | text | Main language of the text (ISO 639-1 code, e.g. `en`, `fr`), detected automatically from the first 3,000 characters. |
| `word_count` | integer | Number of words in `text`. |
| `short_text` | true/false | `True` if `text` has fewer than 20 words (see Section 6). |
| `long_text` | true/false | `True` if `text` has more than 5,000 words (see Section 6). |
| `suspect_text` | true/false | `True` if `text` is known not to correspond to the title (see Section 6). |
| `duplicate_group` | integer | Shared number for all copies of the same document (see Section 7). Empty for documents without copies. |
| `also_in` | text | Institution(s) in which another copy of the document appears, separated by `; `. May include the document's own institution. Empty for documents without copies. |
| `match` | text | How the copy was identified: `url` (same web address), `text` (identical text), `url + text`, or `linked via another copy`. |
| `url` | text | Address of the source page. |
| `scrape_date` | date | Date on which the document was collected. |
| `source_file` | text | Name of the original scraped text file, for traceability. |
| `text` | text | Full text of the document, as captured. |

## 5. How the corpus was built

**Collection.** For each institution, the list of document URLs was collected from the institution's press listing for 2015–2025 (filters as in Section 2), and each page was then visited with an automated browser (Selenium). The title, date and main text of each page were saved; where the content was provided as a PDF, the text of the PDF was extracted. Collection took place between 13 January and 11 February 2026.

**Processing.** Each document's date, time, title and text were separated from the saved file; dates were converted to a common format; documents dated before 2015 were removed; and identifiers, document types, languages and word counts were added. Publication times of exactly 00:00, which the Council website uses where no time is recorded, were set to empty (53 documents).

**What was not changed.** The texts themselves were not edited, cleaned or translated. Boilerplate (e.g. press office contact lines in older Council documents) remains in the text.

**Code.** The script that builds the corpus from the scraped files (`build_eufp_corpus.py`) is available at https://github.com/sasni27/eufp-corpus-2015-2025. It reproduces this version of the corpus exactly from the scraped text files in `eufp_scraped_texts_v1.zip`. To rebuild the corpus: download and extract the zip file, set `INPUT_FOLDER` in the script to the extracted folder, and run the script. Scrape dates are taken from the files' save dates, which the zip file preserves; extract it with a standard tool that keeps file dates.

The scraping code itself is not published: the institutions' websites change over time, so the code would not reproduce the same collection. The scraped files are deposited instead, as a fixed snapshot of what was collected.

## 6. Flags and known issues

| Flag | Documents | Meaning |
|---|---:|---|
| `short_text` | 358 (1.0%) | Fewer than 20 words. Almost always a page whose text was not captured: placeholders such as *Check against delivery*, a video embed, or a speech provided only as an attachment. The URL leads to the original page. |
| `long_text` | 121 (0.3%) | More than 5,000 words. Reports, communiqués, conclusions with annexes, or press releases with an attached legal text (e.g. sanctions lists), rather than standard statements. |
| `suspect_text` | 9 | The text does not correspond to the title, because an attached document was captured instead of the page's own text. `FAC_000023`, `FAC_000024`, `FAC_000078`, `FAC_000082`, `FAC_000089` contain a general Council factsheet on EU restrictive measures (April 2014); `FAC_000334` and `FAC_000341` contain the Afghan National Peace and Development Framework 2017–2021; `EC_000332` contains the statement of the informal meeting of 27 (29 June 2016) instead of the President's remarks; `EC_000368` contains the Bratislava Declaration instead of the President's remarks. |

**Further caveats.**
- **Languages.** 33,191 documents (95.8%) are mainly in English. The remaining 1,443 are mainly European Commission speeches delivered in other EU languages and EEAS statements in Spanish or French. Some English documents contain passages in other languages.
- **Attached documents.** Where a page linked to a PDF, the PDF's text may have been captured. This accounts for some long texts and for the `suspect_text` cases.
- **Incomplete capture.** In a small number of documents only part of the text was captured (e.g. a joint declaration ending at its introductory sentence). These are not systematically flagged.
- **Administrative documents.** The listings include some non-substantive items (e.g. weekly schedules, accreditation notices, lists of participants, meeting agendas). They are retained as published.

## 7. Dual publications and duplicates

The same text is frequently published more than once, either under two institutions or twice by the same institution. These dual publications are retained, as they are themselves informative about institutional communication practice.

**4,173 documents** belong to **2,065 duplicate groups**. Copies were identified by an identical URL, or by identical text after ignoring differences in capitalisation, spacing and line breaks (texts flagged `short_text` were excluded from text matching). The main patterns are:

- **HR and FAC (889 documents in each).** The Council website lists most declarations and statements by the High Representative (many issued *on behalf of the EU*) under both the High Representative and the Foreign Affairs Council.
- **Within the European Commission (2,230 documents).** About 1,100 texts were published twice under different reference numbers, nearly always with the same title.
- **Joint statements.** Statements issued jointly by several presidents (e.g. of the European Council and the European Commission) appear under each signatory institution.
- **Republication.** Some texts are republished by another institution (e.g. EEAS republication of European Council readouts).

## 8. Using the corpus

Loading in Python:

```python
import pandas as pd
corpus = pd.read_parquet("eufp_corpus_v1.parquet")
```

Loading in R:

```r
library(arrow)
corpus <- read_parquet("eufp_corpus_v1.parquet")
```

Common selections (Python):

```python
# English documents with usable text
usable = corpus[(corpus["language"] == "en")
                & ~corpus["short_text"]
                & ~corpus["suspect_text"]]

# One copy per duplicate group within each institution
deduplicated = pd.concat([
    usable[usable["duplicate_group"].isna()],
    usable[usable["duplicate_group"].notna()]
        .drop_duplicates(["institution", "duplicate_group"]),
])
```

Whether HR–FAC copies, joint statements and long texts should be counted for one institution, several, or none depends on the research question; the flag and duplicate columns are provided so that this choice can be made explicitly and reported.

## 9. Licence and reuse

The corpus is released under the [Creative Commons Attribution 4.0 International licence (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). The build code is released under the MIT licence. The underlying texts are public communications of the EU institutions and are reused under their respective reuse policies: for the Council and European Council, Council Decision (EU) 2017/1842 on the open data policy of the Council and the reuse of Council documents; for the European Commission, Commission Decision 2011/833/EU on the reuse of Commission documents; for the EEAS, the legal notice of the EEAS website. Users should acknowledge the original source institution when reproducing or citing texts.

## 10. Citation

If you use the corpus, please cite:

> Nielsen, Sasha Juul. 2026. *EUFP Corpus: EU Foreign Policy Institutional Communication, 2015–2025* (Version 1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.23806268

and, where relevant, the accompanying article:

> Nielsen, Sasha Juul. Forthcoming. "Decoding diplomacy: A large language model approach to emotional rhetoric across EU foreign policy institutions."

## 11. Version history

| Version | Date | Changes |
|---|---|---|
| 1.0 | 30 October 2026 | First public release. |
