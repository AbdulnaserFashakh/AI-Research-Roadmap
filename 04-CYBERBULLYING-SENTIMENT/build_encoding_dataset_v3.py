import csv
import hashlib
import json
import platform
import shutil
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from preview_encoding_repair import REPLACEMENTS
from preview_additional_repairs import RULES
from encoding_rules_v3 import ADDITIONAL_RULES, DEFERRED_FRAGMENTS
from audit_remaining_encoding import extract_fragments

SOURCE = Path("data/raw/tweets_raw.csv")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply_rules(text, rules):
    for damaged, replacement in rules.items():
        text = text.replace(damaged, replacement)
    return text


def main():
    started = datetime.now(timezone.utc)
    run_id = started.strftime("encoding_dataset_v3_%Y%m%dT%H%M%S%fZ")
    folder = Path("experiments") / run_id
    folder.mkdir(parents=True, exist_ok=False)

    combined = {}
    for rule_set in [REPLACEMENTS, RULES, ADDITIONAL_RULES]:
        for damaged, replacement in rule_set.items():
            if damaged in combined and combined[damaged] != replacement:
                raise ValueError("Conflicting rules")
            combined[damaged] = replacement

    if len(combined) != 28:
        raise ValueError(f"Expected 28 rules, found {len(combined)}")

    source_hash = sha256(SOURCE)
    snapshot = folder / "source_snapshot.csv"
    shutil.copy2(SOURCE, snapshot)

    if sha256(snapshot) != source_hash:
        raise RuntimeError("Source snapshot checksum mismatch")

    for script in [
        Path(__file__),
        Path("preview_encoding_repair.py"),
        Path("preview_additional_repairs.py"),
        Path("encoding_rules_v3.py"),
        Path("audit_remaining_encoding.py"),
    ]:
        shutil.copy2(script, folder / script.name)

    rules = [
        {
            "rule_id": f"R{index:02d}",
            "damaged": damaged,
            "replacement": replacement,
        }
        for index, (damaged, replacement) in enumerate(
            combined.items(), start=1
        )
    ]
    (folder / "rules.json").write_text(
        json.dumps({
            "replacement_rules": rules,
            "deferred_fragments": DEFERRED_FRAGMENTS,
        }, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    counts = Counter()
    fragments = Counter()
    examples = {}
    total = changed = flagged = unstable = deferred_rows = 0
    before_unique = set()
    after_unique = set()
    dataset = folder / "dataset_proposed.csv"

    with snapshot.open(encoding="utf-8-sig", newline="") as source:
        with (
            dataset.open("w", encoding="utf-8-sig", newline="") as target,
            (folder / "change_log.csv").open(
                "w", encoding="utf-8-sig", newline=""
            ) as changes_file,
        ):
            reader = csv.DictReader(source)
            if reader.fieldnames != ["text"]:
                raise ValueError(f"Unexpected columns: {reader.fieldnames}")

            writer = csv.DictWriter(target, fieldnames=[
                "row_id", "source_row", "text_original", "text_proposed",
                "changed", "replacement_count", "applied_rules",
                "remaining_candidate_flag", "deferred_fragment_present",
            ])
            changes = csv.DictWriter(changes_file, fieldnames=[
                "row_id", "source_row", "rule_id", "occurrences",
            ])
            writer.writeheader()
            changes.writeheader()

            for index, row in enumerate(reader, start=1):
                original = row.get("text")
                if None in row or original is None:
                    raise ValueError(f"Malformed record: {index}")

                total += 1
                proposed = original
                row_id = f"{source_hash[:16]}_{index:06d}"
                applied = []
                replacement_count = 0

                for rule in rules:
                    count = proposed.count(rule["damaged"])
                    if count:
                        proposed = proposed.replace(
                            rule["damaged"], rule["replacement"]
                        )
                        counts[rule["rule_id"]] += count
                        replacement_count += count
                        applied.append(rule["rule_id"])
                        changes.writerow({
                            "row_id": row_id,
                            "source_row": index,
                            "rule_id": rule["rule_id"],
                            "occurrences": count,
                        })

                unstable += int(
                    apply_rules(proposed, combined) != proposed
                )
                remaining = list(extract_fragments(proposed))
                flagged += int(bool(remaining))

                for fragment in remaining:
                    fragments[fragment] += 1
                    examples.setdefault(fragment, index)

                has_deferred = any(
                    fragment in proposed
                    for fragment in DEFERRED_FRAGMENTS
                )
                deferred_rows += int(has_deferred)
                is_changed = proposed != original
                changed += int(is_changed)
                before_unique.add(original)
                after_unique.add(proposed)

                writer.writerow({
                    "row_id": row_id,
                    "source_row": index,
                    "text_original": original,
                    "text_proposed": proposed,
                    "changed": int(is_changed),
                    "replacement_count": replacement_count,
                    "applied_rules": ";".join(applied),
                    "remaining_candidate_flag": int(bool(remaining)),
                    "deferred_fragment_present": int(has_deferred),
                })

    verified = 0
    with (
        snapshot.open(encoding="utf-8-sig", newline="") as source,
        dataset.open(encoding="utf-8-sig", newline="") as target,
    ):
        derived = csv.DictReader(target)
        for index, row in enumerate(csv.DictReader(source), start=1):
            output = next(derived, None)
            if (
                output is None
                or output["text_original"] != row["text"]
                or int(output["source_row"]) != index
            ):
                raise RuntimeError("Source preservation failed")
            verified += 1

        if next(derived, None) is not None:
            raise RuntimeError("Unexpected extra rows")

    if sha256(SOURCE) != source_hash:
        raise RuntimeError("Source changed during execution")

    with (folder / "remaining_fragments.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=[
            "fragment", "occurrences", "example_source_row",
        ])
        writer.writeheader()
        for fragment, count in fragments.most_common():
            writer.writerow({
                "fragment": fragment,
                "occurrences": count,
                "example_source_row": examples[fragment],
            })

    report = {
        "run_id": run_id,
        "started_utc": started.isoformat(),
        "python_version": platform.python_version(),
        "unicode_database_version": unicodedata.unidata_version,
        "source_sha256": source_hash,
        "rules_count": len(rules),
        "total_rows": total,
        "changed_rows_from_raw": changed,
        "unchanged_rows": total - changed,
        "replacement_occurrences": sum(counts.values()),
        "occurrences_by_rule": {
            rule["rule_id"]: counts[rule["rule_id"]]
            for rule in rules
        },
        "unique_exact_texts_before": len(before_unique),
        "unique_exact_texts_after": len(after_unique),
        "rows_with_remaining_candidate_fragments": flagged,
        "distinct_remaining_candidate_fragments": len(fragments),
        "remaining_fragment_occurrences": sum(fragments.values()),
        "rows_with_deferred_fragment": deferred_rows,
        "idempotence_failure_rows": unstable,
        "verified_original_rows": verified,
        "source_modified": False,
        "rows_removed": 0,
        "normalization_applied": False,
        "labels_created": False,
        "status": "partial_encoding_repair_proposal",
        "limitation": (
            "Exact substring proposals are not globally validated. "
            "Remaining-fragment detection is heuristic and incomplete."
        ),
    }

    (folder / "report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    entry = (
        f"\n\n## Encoding proposal v3 — {run_id}\n\n"
        "- Script: build_encoding_dataset_v3.py\n"
        "- Applied 28 exact rules to a derived copy of the source.\n"
        "- One inspected fragment remains deferred.\n"
        "- Verified original text and record order preservation.\n"
        "- Checked second-pass idempotence and remaining fragments.\n"
        "- No normalization, annotation or row deletion performed.\n"
        "- Archived source, code, rules, changes, dataset and reports.\n"
        "- Proposal remains incomplete and requires review.\n\n"
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
        json.dumps(manifest, indent=2),
        encoding="utf-8",
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
    print("\nTop 10 remaining fragments:")
    for fragment, count in fragments.most_common(10):
        print(json.dumps({
            "fragment": fragment,
            "occurrences": count,
            "example_source_row": examples[fragment],
        }, ensure_ascii=True))


if __name__ == "__main__":
    main()