import csv
import hashlib
import json
import platform
import shutil
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from audit_remaining_encoding_v2 import decoding_candidates
from audit_remaining_encoding import extract_fragments
from encoding_rules_v3 import DEFERRED_FRAGMENTS

INPUT = Path(
    "experiments/encoding_dataset_v3_20261009T192914524945Z/"
    "dataset_proposed.csv"
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_candidate(text):
    return (
        bool(text)
        and "\ufffd" not in text
        and not any(
            unicodedata.category(char) in {"Cc", "Cs", "Cn"}
            for char in text
        )
        and "\u0623" not in text
        and "\u0622" not in text
    )


def contains_arabic(text):
    return any(
        "ARABIC" in unicodedata.name(char, "")
        for char in text
    )


def select_candidate(fragment):
    if any(item in fragment for item in DEFERRED_FRAGMENTS):
        return None, "deferred_fragment", []

    candidates = decoding_candidates(fragment)
    outputs = {
        item["proposed"]
        for item in candidates
        if clean_candidate(item["proposed"])
    }

    # Remove outputs that are still intermediate decoding stages.
    terminal = set()
    for output in outputs:
        further = {
            item["proposed"]
            for item in decoding_candidates(output)
            if clean_candidate(item["proposed"])
        }
        if not further:
            terminal.add(output)

    if len(terminal) != 1:
        status = (
            "no_eligible_terminal_candidate"
            if not terminal
            else "multiple_terminal_candidates"
        )
        return None, status, candidates

    proposed = next(iter(terminal))

    # Arabic output requires separate review.
    if contains_arabic(proposed):
        return None, "arabic_output_requires_review", candidates

    return proposed, "unique_terminal_proposal", candidates


def main():
    started = datetime.now(timezone.utc)
    run_id = started.strftime("encoding_batch_v4_%Y%m%dT%H%M%S%fZ")
    folder = Path("experiments") / run_id
    folder.mkdir(parents=True, exist_ok=False)

    input_hash = sha256(INPUT)
    snapshot = folder / "input_snapshot.csv"
    shutil.copy2(INPUT, snapshot)

    if sha256(snapshot) != input_hash:
        raise RuntimeError("Input snapshot checksum mismatch")

    for script in [
        Path(__file__),
        Path("audit_remaining_encoding_v2.py"),
        Path("audit_remaining_encoding.py"),
        Path("preview_encoding_repair.py"),
        Path("encoding_rules_v3.py"),
    ]:
        shutil.copy2(script, folder / script.name)

    frequencies = Counter()
    examples = {}

    with snapshot.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            for fragment in extract_fragments(row["text_proposed"]):
                frequencies[fragment] += 1
                examples.setdefault(fragment, row["source_row"])

    decisions = {}
    statuses = Counter()

    for fragment in frequencies:
        proposed, status, candidates = select_candidate(fragment)
        decisions[fragment] = (proposed, status, candidates)
        statuses[status] += 1

    with (folder / "fragment_decisions.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=[
            "fragment", "occurrences", "example_source_row",
            "status", "proposed", "candidates", "review_decision",
        ])
        writer.writeheader()
        for fragment, count in frequencies.most_common():
            proposed, status, candidates = decisions[fragment]
            writer.writerow({
                "fragment": fragment,
                "occurrences": count,
                "example_source_row": examples[fragment],
                "status": status,
                "proposed": proposed or "",
                "candidates": json.dumps(candidates, ensure_ascii=True),
                "review_decision": "",
            })

    output = folder / "dataset_proposed.csv"
    total = additional_changed = changed_from_raw = unresolved_rows = 0
    replacement_occurrences = 0
    remaining_counts = Counter()

    with snapshot.open(encoding="utf-8-sig", newline="") as source:
        with (
            output.open("w", encoding="utf-8-sig", newline="") as target,
            (folder / "change_log.csv").open(
                "w", encoding="utf-8-sig", newline=""
            ) as changes_file,
        ):
            writer = csv.DictWriter(target, fieldnames=[
                "row_id", "source_row", "text_original",
                "text_before_batch", "text_proposed",
                "changed_in_batch", "changed_from_raw",
                "remaining_candidate_flag",
            ])
            changes = csv.DictWriter(changes_file, fieldnames=[
                "row_id", "source_row", "fragment",
                "replacement", "occurrences",
            ])
            writer.writeheader()
            changes.writeheader()

            for row in csv.DictReader(source):
                total += 1
                before = row["text_proposed"]
                after = before
                fragment_list = list(extract_fragments(before))

                # Replace only complete extracted fragments.
                # Process from right to left to preserve character positions.
                spans = []
                cursor = 0
                for fragment in fragment_list:
                    start = before.find(fragment, cursor)
                    if start < 0:
                        raise RuntimeError("Fragment position not found")
                    spans.append((start, start + len(fragment), fragment))
                    cursor = start + len(fragment)

                applied = Counter()
                for start, end, fragment in reversed(spans):
                    proposed = decisions[fragment][0]
                    if proposed is not None:
                        after = after[:start] + proposed + after[end:]
                        applied[fragment] += 1

                for fragment, count in applied.items():
                    changes.writerow({
                        "row_id": row["row_id"],
                        "source_row": row["source_row"],
                        "fragment": fragment,
                        "replacement": decisions[fragment][0],
                        "occurrences": count,
                    })
                    replacement_occurrences += count

                remaining = list(extract_fragments(after))
                remaining_counts.update(remaining)
                unresolved_rows += int(bool(remaining))
                additional_changed += int(after != before)
                changed_from_raw += int(after != row["text_original"])

                writer.writerow({
                    "row_id": row["row_id"],
                    "source_row": row["source_row"],
                    "text_original": row["text_original"],
                    "text_before_batch": before,
                    "text_proposed": after,
                    "changed_in_batch": int(after != before),
                    "changed_from_raw": int(after != row["text_original"]),
                    "remaining_candidate_flag": int(bool(remaining)),
                })

    verified = 0
    with (
        snapshot.open(encoding="utf-8-sig", newline="") as source,
        output.open(encoding="utf-8-sig", newline="") as target,
    ):
        outputs = csv.DictReader(target)
        for original in csv.DictReader(source):
            derived = next(outputs, None)
            if derived is None or any(
                original[key] != derived[key]
                for key in ["row_id", "source_row", "text_original"]
            ):
                raise RuntimeError("Preservation verification failed")
            verified += 1
        if next(outputs, None) is not None:
            raise RuntimeError("Unexpected extra rows")

    if sha256(INPUT) != input_hash:
        raise RuntimeError("Input changed during execution")

    with (folder / "remaining_fragments.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["fragment", "occurrences"])
        writer.writerows(remaining_counts.most_common())

    report = {
        "run_id": run_id,
        "python_version": platform.python_version(),
        "unicode_database_version": unicodedata.unidata_version,
        "input_sha256": input_hash,
        "total_rows": total,
        "distinct_fragments_examined": len(decisions),
        "fragment_decision_counts": dict(statuses),
        "rows_changed_in_batch": additional_changed,
        "rows_changed_from_raw": changed_from_raw,
        "batch_fragment_replacement_occurrences": replacement_occurrences,
        "rows_with_remaining_candidate_fragments": unresolved_rows,
        "distinct_remaining_candidate_fragments": len(remaining_counts),
        "verified_preserved_rows": verified,
        "input_modified": False,
        "rows_removed": 0,
        "normalization_applied": False,
        "labels_created": False,
        "status": "automated_encoding_proposal_requires_review",
        "limitation": (
            "Unique reversible terminal decoding is a selection heuristic, "
            "not proof of intended text. Detection misses defects outside "
            "the observed extraction markers. Arabic outputs are deferred."
        ),
    }

    (folder / "report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    entry = (
        f"\n\n## Batch encoding proposal — {run_id}\n\n"
        "- Script: build_encoding_batch_v4.py\n"
        "- Examined all extracted fragments in encoding proposal v3.\n"
        "- Selected one clean terminal reversible output where available.\n"
        "- Deferred ambiguous, Arabic-output and previously deferred cases.\n"
        "- Replaced complete extracted spans, not arbitrary substrings.\n"
        "- Retained raw text, prior proposal, identifiers and row order.\n"
        "- No normalization, annotation or row deletion performed.\n"
        "- Automated proposals require contextual validation.\n\n"
        "```json\n" + json.dumps(report, indent=2) + "\n```\n"
    )
    (folder / "methods_entry.md").write_text(entry, encoding="utf-8")

    manifest = [
        {
            "file": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(folder.iterdir())
        if path.is_file()
    ]
    (folder / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    results = Path("results")
    results.mkdir(exist_ok=True)
    for name in ["report", "manifest"]:
        shutil.copy2(
            folder / f"{name}.json",
            results / f"{run_id}_{name}.json",
        )

    with Path("METHODS_LOG.md").open("a", encoding="utf-8") as file:
        file.write(entry)

    print(json.dumps(report, indent=2))
    print("Experiment saved:", folder)
    print("METHODS_LOG.md updated.")


if __name__ == "__main__":
    main()