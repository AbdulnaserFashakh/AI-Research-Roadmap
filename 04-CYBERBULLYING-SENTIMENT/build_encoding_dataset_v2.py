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
from audit_remaining_encoding import extract_fragments

SOURCE = Path("data/raw/tweets_raw.csv")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started = datetime.now(timezone.utc)
    run_id = started.strftime("encoding_dataset_v2_%Y%m%dT%H%M%S%fZ")
    folder = Path("experiments") / run_id
    folder.mkdir(parents=True, exist_ok=False)

    source_hash = sha256(SOURCE)

    combined = dict(REPLACEMENTS)
    for damaged, replacement in RULES.items():
        if damaged in combined and combined[damaged] != replacement:
            raise ValueError("Conflicting replacement rules")
        combined[damaged] = replacement

    if len(combined) != 19:
        raise ValueError(f"Expected 19 rules, found {len(combined)}")

    scripts = [
        Path(__file__),
        Path("preview_encoding_repair.py"),
        Path("preview_additional_repairs.py"),
        Path("audit_remaining_encoding.py"),
    ]

    for script in scripts:
        shutil.copy2(script, folder / script.name)

    shutil.copy2(SOURCE, folder / "source_snapshot.csv")
    if sha256(folder / "source_snapshot.csv") != source_hash:
        raise RuntimeError("Source snapshot checksum mismatch")

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
        json.dumps(rules, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    rule_counts = Counter()
    fragment_counts = Counter()
    fragment_examples = {}
    total = changed = flagged = 0
    idempotence_failures = 0
    exact_before = set()
    exact_after = set()

    dataset = folder / "dataset_proposed.csv"

    with SOURCE.open(encoding="utf-8-sig", newline="") as source:
        with (
            dataset.open("w", encoding="utf-8-sig", newline="") as data_file,
            (folder / "change_log.csv").open(
                "w", encoding="utf-8-sig", newline=""
            ) as change_file,
        ):
            reader = csv.DictReader(source)
            if reader.fieldnames != ["text"]:
                raise ValueError(f"Unexpected columns: {reader.fieldnames}")

            writer = csv.DictWriter(data_file, fieldnames=[
                "row_id", "source_row", "text_original", "text_proposed",
                "changed", "replacement_count", "applied_rules",
                "remaining_candidate_flag",
            ])
            changes = csv.DictWriter(change_file, fieldnames=[
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
                applied = []
                replacements = 0
                row_id = f"{source_hash[:16]}_{index:06d}"

                for rule in rules:
                    count = proposed.count(rule["damaged"])
                    if count:
                        proposed = proposed.replace(
                            rule["damaged"], rule["replacement"]
                        )
                        rule_counts[rule["rule_id"]] += count
                        replacements += count
                        applied.append(rule["rule_id"])
                        changes.writerow({
                            "row_id": row_id,
                            "source_row": index,
                            "rule_id": rule["rule_id"],
                            "occurrences": count,
                        })

                # Verify that rerunning the same rules makes no further change.
                second_pass = proposed
                for rule in rules:
                    second_pass = second_pass.replace(
                        rule["damaged"], rule["replacement"]
                    )
                idempotence_failures += int(second_pass != proposed)

                fragments = list(extract_fragments(proposed))
                flagged += int(bool(fragments))

                for fragment in fragments:
                    fragment_counts[fragment] += 1
                    fragment_examples.setdefault(fragment, index)

                is_changed = proposed != original
                changed += int(is_changed)
                exact_before.add(original)
                exact_after.add(proposed)

                writer.writerow({
                    "row_id": row_id,
                    "source_row": index,
                    "text_original": original,
                    "text_proposed": proposed,
                    "changed": int(is_changed),
                    "replacement_count": replacements,
                    "applied_rules": ";".join(applied),
                    "remaining_candidate_flag": int(bool(fragments)),
                })

    # Verify preservation against the archived source.
    verified = 0
    with (
        (folder / "source_snapshot.csv").open(
            encoding="utf-8-sig", newline=""
        ) as source,
        dataset.open(encoding="utf-8-sig", newline="") as derived,
    ):
        outputs = csv.DictReader(derived)
        for row in csv.DictReader(source):
            output_row = next(outputs, None)
            if output_row is None or row["text"] != output_row["text_original"]:
                raise RuntimeError("Original text preservation failed")
            verified += 1
        if next(outputs, None) is not None:
            raise RuntimeError("Unexpected extra output rows")

    if sha256(SOURCE) != source_hash:
        raise RuntimeError("Source changed during execution")

    with (folder / "remaining_fragments.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=[
            "fragment", "occurrences", "example_source_row",
        ])
        writer.writeheader()
        for fragment, count in fragment_counts.most_common():
            writer.writerow({
                "fragment": fragment,
                "occurrences": count,
                "example_source_row": fragment_examples[fragment],
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
        "replacement_occurrences": sum(rule_counts.values()),
        "occurrences_by_rule": {
            rule["rule_id"]: rule_counts[rule["rule_id"]]
            for rule in rules
        },
        "unique_exact_texts_before": len(exact_before),
        "unique_exact_texts_after": len(exact_after),
        "rows_with_remaining_candidate_fragments": flagged,
        "distinct_remaining_candidate_fragments": len(fragment_counts),
        "remaining_fragment_occurrences": sum(fragment_counts.values()),
        "idempotence_failure_rows": idempotence_failures,
        "verified_original_rows": verified,
        "source_modified": False,
        "rows_removed": 0,
        "normalization_applied": False,
        "labels_created": False,
        "status": "partial_encoding_repair_proposal",
        "limitation": (
            "Remaining-fragment detection is heuristic and incomplete. "
            "Repair proposals have not received global human validation."
        ),
    }

    (folder / "report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    methods = (
        f"\n\n## Encoding dataset proposal v2 — {run_id}\n\n"
        "- Script: build_encoding_dataset_v2.py\n"
        "- Applied 19 exact replacement rules to a derived copy.\n"
        "- No Unicode normalization or label creation performed.\n"
        "- Preserved and verified every original text and source row.\n"
        "- Assessed exact-text counts and second-pass idempotence.\n"
        "- Audited remaining fragments using the existing heuristic.\n"
        "- Counts of changed rows are measured directly against raw text.\n"
        "- Source, code, rules, dataset, change log, remaining fragments,\n"
        "  report and manifest are archived in the experiment directory.\n"
        "- This dataset remains a partial repair proposal.\n\n"
        "Execution results:\n\n```json\n"
        + json.dumps(report, indent=2)
        + "\n```\n"
    )
    (folder / "methods_entry.md").write_text(methods, encoding="utf-8")

    manifest = [
        {
            "file": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(folder.iterdir())
        if path.is_file()
    ]
    manifest_file = folder / "manifest.json"
    manifest_file.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    results = Path("results")
    results.mkdir(exist_ok=True)
    shutil.copy2(folder / "report.json", results / f"{run_id}_report.json")
    shutil.copy2(manifest_file, results / f"{run_id}_manifest.json")

    with Path("METHODS_LOG.md").open("a", encoding="utf-8") as file:
        file.write(methods)

    print(json.dumps(report, indent=2))
    print("Experiment saved:", folder)
    print("METHODS_LOG.md updated.")


if __name__ == "__main__":
    main()