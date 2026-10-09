# Methods and Execution Log

## Study objective

Evaluate whether explicit sentiment integration changes abuse-detection
errors across target groups through a controlled comparison of the
same model with and without sentiment information.

This objective has not yet been tested.
Target-group definitions and annotation guidelines remain under development.

## Documentation policy

For each step, record:
- Script and relevant functions.
- Input and output paths.
- Parameters and software versions.
- Observed results.
- Changes made to the data.
- Validation performed and unresolved limitations.

Distinguish executed procedures from proposed procedures.
Do not treat reviewed examples as validation of the entire dataset.

## 1. Execution environment

- Local Windows computer.
- Editor: Visual Studio Code.
- Terminal: PowerShell.
- Python version reported by the interpreter: 3.14.7.
- Project-specific virtual environment: .venv.
- Display adapter reported: Intel(R) UHD Graphics.
- The nvidia-smi command was unavailable.
- No GPU training has been performed.
- No third-party Python packages were required for the executed scripts.

Project directory:
C:\Users\lenovo\AI-Research-Roadmap\04-CYBERBULLYING-SENTIMENT

## 2. Working dataset

Input: data/raw/tweets_raw.csv

The working file contains one column named text.
Legacy labels were removed from the working copy.

SHA-256:
bfeb77e512a90d2a02942f1c7aba1288e308e7486db2881d347038b42d4859ea

A separate five-column comparison file was retained:
data/raw/tweets_original.csv

Columns:
text, created_at, cyberbullying_type, sub_category, emotions

SHA-256:
869510601196dd8d43d30b9478bed33072303b9c001bca3d6f828ff8f079fc02

The provenance of this comparison file before the current workflow
has not been independently verified.

Legacy labels have not been used as new annotations or model inputs.

## 3. Initial raw-data audit

Script: audit_raw.py
Function: main()

Input:
data/raw/tweets_raw.csv

Output:
results/raw_audit.json

Procedure:
- Read CSV using utf-8-sig and csv.DictReader.
- Require a single column named text.
- Check malformed records and whitespace-only texts.
- Count exact duplicate texts without normalizing them.
- Calculate the source SHA-256.
- Record the Python version and execution timestamp.

Results:
- Total rows: 58,316.
- Empty texts: 0.
- Nonempty texts: 58,316.
- Unique nonempty texts by exact matching: 51,529.
- Duplicate excess rows by exact matching: 6,787.

Duplicate excess means occurrences beyond the first occurrence.
It does not mean the number of duplicate groups.

No source rows or texts were changed.

Git commit:
ff3ebb0 — Add raw tweet audit and exclude local data

## 4. Normalization for duplicate grouping

Script: group_duplicates.py
Functions:
- normalize_for_grouping(text)
- main()

Input:
data/raw/tweets_raw.csv

Outputs:
- data/processed/tweets_grouped.csv
- results/duplicate_groups.json

Normalization sequence:
1. unicodedata.normalize("NFKC", text)
2. casefold()
3. Split and rejoin whitespace using a single space.

Normalization was applied only to calculate grouping identifiers.
The original text was retained in the output.

Identifier construction:
- row_id: first 16 characters of source SHA-256 plus one-based CSV record index.
- group_id: SHA-256 of the normalized text encoded as UTF-8.
- group_size: number of source records sharing the group_id.

Results:
- Total rows: 58,316.
- Normalized text groups: 51,487.
- Duplicate excess rows: 6,829.
- Groups containing multiple rows: 2,958.
- Largest group: 20 rows.
- Additional duplicate excess compared with exact matching: 42.
- Rows removed: 0.

Limitations:
- Semantic and near duplicates were not assessed.
- A shared group_id does not establish identical annotations.
- Grouping must be recalculated after encoding repair.
- No train/validation/test split has been created.

Git commit:
7e84806 — Group duplicate tweets while preserving original text

## 5. Annotation-guideline pilot

Script: create_review_sample.py
Function: main()

Input:
data/processed/tweets_grouped.csv

Outputs:
- data/review/pilot_100.csv
- results/pilot_100_manifest.json

Procedure:
- Retain the first source row as representative of each group.
- Sort group identifiers.
- Sample 100 groups without replacement.
- Use random.Random(42).
- Leave annotation fields blank.
- Record selected group identifiers and input/output SHA-256 values.
- Refuse to overwrite an existing pilot CSV.

Annotation fields:
abuse_label, mentioned_groups, targeted_groups, sentiment,
uncertain, rationale, annotator_id

Purpose:
Test and refine annotation guidelines.
This is not a held-out evaluation dataset.

Five texts received preliminary discussion in the conversation.
Those judgments were not independently validated and were not
confirmed as saved annotations.

Annotation decisions still required:
- Operational definition of abuse.
- Distinction between abuse and cyberbullying.
- Mentioned versus targeted groups.
- Multi-label group representation.
- Treatment of sexual orientation relative to gender.
- Sentiment scope and uncertain cases.
- Independent review and disagreement resolution.

## 6. Encoding inspection

Script: check_encoding.py

Outputs generated across two script versions:
- results/encoding_check.json
- results/raw_encoding_check.json

Inspected source record indices:
4,186; 6,436; 56,335.

Procedure:
Read texts as UTF-8 and display their stored characters
using JSON Unicode escapes.

Finding:
Malformed character sequences were present in both the pilot
and the working raw CSV.
The issue was not solely terminal display.

Reproducibility limitation:
check_encoding.py was subsequently replaced with the raw-file
inspection version. The earlier pilot inspection is therefore
not reproduced by the current script without modification.

## 7. Full text-preservation comparison

Script: compare_encoding.py
Functions:
- inspect(path)
- read_texts(path), defined within main()
- main()

Inputs:
- data/raw/tweets_original.csv
- data/raw/tweets_raw.csv

Output:
results/encoding_comparison.json

Results:
- Both files decoded successfully as UTF-8.
- Both contained 58,316 records.
- All text values matched in the same order.
- Different paired rows: 0.
- The three inspected texts contained the same malformed sequences.

Interpretation:
Removing legacy columns preserved the text values in the
two compared files.

This comparison does not establish when the encoding damage arose.
Valid UTF-8 does not prove that text is free of prior decoding damage.

Neither input was modified.

## 8. Encoding-pattern audit

Script: audit_encoding_patterns.py
Function: main()

Input:
data/raw/tweets_raw.csv

Outputs:
- results/encoding_patterns.json
- data/review/encoding_candidates.csv

Patterns inspected:
- \u0623\u00a2\u0622
- \u0623\u00a3
- \ufffd

Results:
- Total rows: 58,316.
- Rows matching at least one pattern: 9,071.
- Rows matching the first pattern: 8,956.
- Rows matching the second pattern: 118.
- Rows containing U+FFFD: 0.
- Rows matching both the first and second patterns: 3.
- Repairs applied: 0.

Pattern counts refer to rows, not individual occurrences.

Limitations:
Matches are candidates for review.
The patterns do not cover all possible encoding defects.
Absence of U+FFFD does not establish intact text.

## 9. Proposed punctuation repair

Script: preview_encoding_repair.py
Function: main()

Input:
data/review/encoding_candidates.csv

Output:
data/review/encoding_repair_preview.csv

Exact replacement rules:
- \u0623\u00a2\u0622\u20ac\u0622\u2122 -> U+2019
- \u0623\u00a2\u0622\u20ac\u0622\u0153 -> U+201C
- \u0623\u00a2\u0622\u20ac\u0622\u200c -> U+201D
- \u0623\u00a2\u0622\u20ac\u0622\u201d -> U+2014
- \u0623\u00a2\u0622\u20ac\u0622\u00a6 -> U+2026

Output fields:
source_row, text_original, text_proposed,
replacement_count, review_decision

Results:
- Rows with proposed changes: 8,641.
- Original source unchanged.
- review_decision remains blank.
- Output contains changed candidate rows only.

Review performed:
- Before/after examples inspected at source rows 1, 10 and 23.
- First available example displayed for each replacement rule.
- Rule examples occurred at rows 1, 75 and 77.
- Apostrophe, quotation-mark and ellipsis changes were
  consistent with the displayed examples.
- The dash example at row 75 remains less contextually clear.

Status:
Proposed repair, not globally validated or approved for training.

Unresolved:
- Corrupted emoji sequences.
- Other encoding defects outside the inspected patterns.
- HTML entities such as &amp; and &lt; remain unchanged.
- No spelling, grammatical wording or abusive terms were removed.
- No complete repaired dataset has been created.

The preview must not be used as the full training dataset.

## 10. Version-control and file locations

Project .gitignore excludes:
.venv/
data/
__pycache__/
*.pyc

Code is stored in the project root.
Data and text-bearing review files are stored under data/.
Audit reports are stored under results/.

check_encoding.py and compare_encoding.py were moved from
data/review/ to the project root for version control.

Additional commits were reported as completed for:
- Encoding inspection and preservation comparison.

Their hashes have not been recorded in this log.

The pilot and subsequent encoding/repair scripts require a
Git status check to confirm their current commit status.

Encoding inspection reports contain tweet excerpts.
No upload to the remote repository was confirmed in this workflow.

## 11. Current study status

Completed:
- Raw-data audit.
- Exact and normalized duplicate analysis.
- Reproducible pilot sampling.
- Full comparison of text preservation.
- Audit of selected encoding patterns.
- Proposed punctuation-repair preview.

Not completed:
- Full encoding repair and validation.
- Final normalization policy for model inputs.
- Revised duplicate grouping after repair.
- Final annotation guidelines.
- Independent annotation and adjudication.
- Train/validation/test split.
- Training-set balancing.
- Model selection and training.
- Sentiment ablation.
- Target-group FPR/FNR analysis.

No model-performance or research-novelty conclusion follows
from the preparation steps alone.

## 12. Next procedures

1. Validate and document encoding-repair rules.
2. Address emoji and remaining encoding defects.
3. Create a complete derived dataset with preserved source text.
4. Recalculate duplicate groups.
5. Finalize and test annotation guidelines.
6. Establish reviewed labels.
7. Split by groups before any training-set balancing.
8. Fit learned preprocessing on training data only.
9. Compare the same model with and without sentiment.
10. Report overall and group-specific errors with uncertainty.
## Encoding repair preview — version 2

- Input: data/raw/tweets_raw.csv
- Script: preview_encoding_repair.py
- Rules: five punctuation rules and four emoji rules.
- Emoji decoding path: cp1256 followed by latin1.
- Exact round-trip reconstruction verified for four tested fragments.
- Total source rows: 58,316.
- Rows with proposed changes: 8,877.
- Replacement occurrences: 18,821.
- Additional changed rows compared with version 1: 236.
- Preview: data/review/encoding_repair_preview.csv
- Report: results/encoding_repair_preview.json
- Source unchanged.
- Preview contains changed rows only.
- Remaining encoding defects are unresolved.
- Global annotation review has not been completed.
- Version 1 preview CSV was overwritten by this execution.
- Version 1 code remains available in Git history.
- A separate archive copy was requested, but its creation is unconfirmed.
## Emoji probe code restoration

- Identical SHA-256 hashes revealed that inspect_emoji_repair.py
  contained the preview script instead of the probe script.
- The misnamed code was preserved in
  archive/inspect_emoji_repair_misnamed.py.
- The probe code was restored and rerun.
- Output: results/emoji_repair_probe_restored.json.
- Fragment occurrence counts were reproduced: 44, 17, 771 and 48.
- Each fragment had one reversible cp1256/latin1 decoding candidate.
- The source SHA-256 matched the prior raw-data audit.
- Restored code and output were copied into experiments/encoding_v2
  under separate filenames.
- No source text was modified.
## Remaining encoding audit — version 1

- Script: audit_remaining_encoding.py
- Existing nine repair rules were applied in memory only.
- Rows with remaining candidate fragments: 2,839.
- Distinct candidate fragments: 1,316.
- Candidate fragment occurrences: 4,727.
- No source modification or additional repair was performed.
- Extraction may flag genuine Arabic and miss other defects.
- Candidate decoding tested two stages only.
- Single-stage decoding was not tested in this version.
- Code, dependency script, report and fragment table were archived
  locally under experiments/remaining_encoding_v1.

  ## Remaining encoding candidates — version 2

- Script: audit_remaining_encoding_v2.py
- Tested reversible one-stage and two-stage decoding.
- Distinct fragments tested: 1,316.
- No candidate: 145 fragments.
- One distinct output: 82 fragments.
- Multiple distinct outputs: 1,089 fragments.
- Multiple outputs can include an intermediate damaged string
  and a further decoded string, rather than conflicting final repairs.
- Inspected examples recovered accented letters, punctuation,
  symbols and emoji.
- Reversibility alone does not establish the intended source text.
- No new repairs were applied.
- Input and script SHA-256 values are recorded in the report.
- Code, input fragment table and outputs were archived locally
  under experiments/remaining_encoding_v2.

  ## Encoding candidate screening — version 1

- Script: screen_encoding_candidates.py
- Fragments with one retained output: 915.
- Fragments with multiple retained outputs: 61.
- Fragments without decoding candidates: 145.
- Fragments with all candidates excluded by the heuristic: 195.
- Counts describe distinct fragments, not tweets.
- Context previews supported several accented-letter,
  punctuation and emoji candidates.
- Previews also revealed encoding damage outside the extraction
  markers, including the sequence U+00E2 U+20AC U+2122.
- Context previews replaced the inspected fragment only.
- Heuristic exclusions are not confirmed decoding failures.
- No repair was applied to the source dataset.
- Code, input candidate table and outputs were archived under
  experiments/encoding_screen_v1.
  ## Complete derived dataset — encoding proposal v1

- Run ID: encoding_dataset_v1_20261009T184159656645Z
- Script: build_encoding_dataset_v1.py
- Python: 3.14.7
- Rules: 9 exact replacements.
- Total rows: 58,316.
- Changed rows: 8,877.
- Unchanged rows: 49,439.
- Replacement occurrences: 18,821.
- Occurrences by rule:
  R01=10,757; R02=2,994; R03=2,927; R04=291; R05=972;
  R06=44; R07=17; R08=771; R09=48.
- Original text preservation verified for all 58,316 rows.
- No source modification or row removal.
- No normalization or label creation in this run.
- Encoding repair remains partial and proposed.

Experiment directory:
experiments/encoding_dataset_v1_20261009T184159656645Z

Archived artifacts:
source snapshot, executed script, dependency script, rules,
complete proposed dataset, change log, report and SHA-256 manifest.
The manifest covers the other archived files, not itself.

## Additional repair proposals — version 1

- Run ID: additional_repairs_20261009T184437845002Z
- Script: preview_additional_repairs.py
- Input: complete nine-rule derived dataset.
- Input SHA-256:
  824e0d2b6390c6b5ca09561a0486c4598e60f8377db839e413a67c76eccc478d
- Additional rules: 10 exact substring replacements.
- Total rows inspected: 58,316.
- Rows with additional proposals: 882.
- Replacement occurrences: 1,695.
- Input unchanged.
- Output contains changed rows only.
- These rows may overlap with previously changed rows.
- Substring replacement counts differ from whole-fragment
  extraction counts and must not be treated as equivalent.
- Proposals remain subject to contextual review.
- Input snapshot, code, preview, report and manifest were archived
  in the experiment directory.

  ## Additional repair boundary audit

- Run ID: repair_boundaries_20261009T184651176311Z
- Script: review_repair_boundaries.py
- Total rows inspected: 58,316.
- Whole extracted-fragment match occurrences: 1,195.
- Match occurrences inside longer fragments: 500.
- Total matched occurrences: 1,695.
- Distinct rule/fragment pairs: 141.
- Five displayed longer-fragment examples involved adjacent
  or repeated emoji sequences.
- Some surrounding emoji sequences remained damaged.
- These examples do not validate all longer-fragment matches.
- No input modification or repair application.
- Code, dependencies, input snapshot, review table, report
  and manifest were archived in the experiment directory.

  ## Contextual review of ten remaining fragments

- Probe run: remaining_top10_20261009T192255202836Z.
- Nine final decoding outputs were supported by the displayed contexts.
- Single-stage intermediate damaged outputs were not selected.
- Two decoding paths produced the same final é output.
- Nine exact proposals were recorded in encoding_rules_v3.py.
- One fragment was deferred because it decoded to two Arabic
  fathatan marks with unexplained usage in the displayed context.
- No new replacements have yet been applied.
- These decisions concern inspected examples, not validation
  of every occurrence across the dataset.

## References

Python CSV:
https://docs.python.org/3/library/csv.html

Unicode normalization:
https://docs.python.org/3/library/unicodedata.html

Unicode handling:
https://docs.python.org/3/howto/unicode.html

Grouped data splitting:
https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html

Data leakage:
https://scikit-learn.org/stable/common_pitfalls.html#data-leakage

## Encoding dataset proposal v2 — encoding_dataset_v2_20261009T192006935492Z

- Script: build_encoding_dataset_v2.py
- Applied 19 exact replacement rules to a derived copy.
- No Unicode normalization or label creation performed.
- Preserved and verified every original text and source row.
- Assessed exact-text counts and second-pass idempotence.
- Audited remaining fragments using the existing heuristic.
- Counts of changed rows are measured directly against raw text.
- Source, code, rules, dataset, change log, remaining fragments,
  report and manifest are archived in the experiment directory.
- This dataset remains a partial repair proposal.

Execution results:

```json
{
  "run_id": "encoding_dataset_v2_20261009T192006935492Z",
  "started_utc": "2026-10-09T19:20:06.935492+00:00",
  "python_version": "3.14.7",
  "unicode_database_version": "16.0.0",
  "source_sha256": "bfeb77e512a90d2a02942f1c7aba1288e308e7486db2881d347038b42d4859ea",
  "rules_count": 19,
  "total_rows": 58316,
  "changed_rows_from_raw": 9405,
  "unchanged_rows": 48911,
  "replacement_occurrences": 20516,
  "occurrences_by_rule": {
    "R01": 10757,
    "R02": 2994,
    "R03": 2927,
    "R04": 291,
    "R05": 972,
    "R06": 44,
    "R07": 17,
    "R08": 771,
    "R09": 48,
    "R10": 271,
    "R11": 269,
    "R12": 131,
    "R13": 251,
    "R14": 334,
    "R15": 93,
    "R16": 69,
    "R17": 74,
    "R18": 134,
    "R19": 69
  },
  "unique_exact_texts_before": 51529,
  "unique_exact_texts_after": 51529,
  "rows_with_remaining_candidate_fragments": 2201,
  "distinct_remaining_candidate_fragments": 1256,
  "remaining_fragment_occurrences": 3455,
  "idempotence_failure_rows": 0,
  "verified_original_rows": 58316,
  "source_modified": false,
  "rows_removed": 0,
  "normalization_applied": false,
  "labels_created": false,
  "status": "partial_encoding_repair_proposal",
  "limitation": "Remaining-fragment detection is heuristic and incomplete. Repair proposals have not received global human validation."
}
```


## Remaining-fragment probe — remaining_top10_20261009T192255202836Z
- Script: probe_remaining_top10.py
- Examined the ten most frequent remaining fragments.
- Tested reversible one-stage and two-stage decoding.
- Preserved contextual previews and code in the experiment.
- Input dataset identified by SHA-256 in report.json.
- No repairs applied. Candidates require contextual review.


## Encoding proposal v3 — encoding_dataset_v3_20261009T192914524945Z

- Script: build_encoding_dataset_v3.py
- Applied 28 exact rules to a derived copy of the source.
- One inspected fragment remains deferred.
- Verified original text and record order preservation.
- Checked second-pass idempotence and remaining fragments.
- No normalization, annotation or row deletion performed.
- Archived source, code, rules, changes, dataset and reports.
- Proposal remains incomplete and requires review.

```json
{
  "run_id": "encoding_dataset_v3_20261009T192914524945Z",
  "started_utc": "2026-10-09T19:29:14.524945+00:00",
  "python_version": "3.14.7",
  "unicode_database_version": "16.0.0",
  "source_sha256": "bfeb77e512a90d2a02942f1c7aba1288e308e7486db2881d347038b42d4859ea",
  "rules_count": 28,
  "total_rows": 58316,
  "changed_rows_from_raw": 9691,
  "unchanged_rows": 48625,
  "replacement_occurrences": 21163,
  "occurrences_by_rule": {
    "R01": 10757,
    "R02": 2994,
    "R03": 2927,
    "R04": 291,
    "R05": 972,
    "R06": 44,
    "R07": 17,
    "R08": 771,
    "R09": 48,
    "R10": 271,
    "R11": 269,
    "R12": 131,
    "R13": 251,
    "R14": 334,
    "R15": 93,
    "R16": 69,
    "R17": 74,
    "R18": 134,
    "R19": 69,
    "R20": 60,
    "R21": 96,
    "R22": 50,
    "R23": 114,
    "R24": 75,
    "R25": 67,
    "R26": 42,
    "R27": 92,
    "R28": 51
  },
  "unique_exact_texts_before": 51529,
  "unique_exact_texts_after": 51529,
  "rows_with_remaining_candidate_fragments": 1900,
  "distinct_remaining_candidate_fragments": 1203,
  "remaining_fragment_occurrences": 2992,
  "rows_with_deferred_fragment": 42,
  "idempotence_failure_rows": 0,
  "verified_original_rows": 58316,
  "source_modified": false,
  "rows_removed": 0,
  "normalization_applied": false,
  "labels_created": false,
  "status": "partial_encoding_repair_proposal",
  "limitation": "Exact substring proposals are not globally validated. Remaining-fragment detection is heuristic and incomplete."
}
```
