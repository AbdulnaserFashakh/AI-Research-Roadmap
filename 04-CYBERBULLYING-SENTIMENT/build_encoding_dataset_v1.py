import csv
import hashlib
import json
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path

from preview_encoding_repair import REPLACEMENTS

SOURCE = Path("data/raw/tweets_raw.csv")
RULES_SCRIPT = Path("preview_encoding_repair.py")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started = datetime.now(timezone.utc)
    run_id = started.strftime("encoding_dataset_v1_%Y%m%dT%H%M%S%fZ")
    run_dir = Path("experiments") / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    source_hash = sha256(SOURCE)

    # Preserve the source, executed code and dependency.
    shutil.copy2(SOURCE, run_dir / "source_snapshot.csv")
    shutil.copy2(Path(__file__), run_dir / "build_encoding_dataset_v1.py")
    shutil.copy2(RULES_SCRIPT, run_dir / "preview_encoding_repair.py")

    if sha256(run_dir / "source_snapshot.csv") != source_hash:
        raise RuntimeError("Source snapshot checksum mismatch")

    rules = [
        {
            "rule_id": f"R{index:02d}",
            "damaged": damaged,
            "replacement": replacement,
        }
        for index, (damaged, replacement) in enumerate(
            REPLACEMENTS.items(), start=1
        )
    ]

    (run_dir / "rules.json").write_text(
        json.dumps(rules, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    dataset = run_dir / "dataset_proposed.csv"
    changes = run_dir / "change_log.csv"
    counts = {rule["rule_id"]: 0 for rule in rules}
    total = changed = 0

    with SOURCE.open(encoding="utf-8-sig", newline="") as source:
        with (
            dataset.open("w", encoding="utf-8-sig", newline="") as data_file,
            changes.open("w", encoding="utf-8-sig", newline="") as change_file,
        ):
            reader = csv.DictReader(source)

            if reader.fieldnames != ["text"]:
                raise ValueError(f"Unexpected columns: {reader.fieldnames}")

            data_writer = csv.DictWriter(data_file, fieldnames=[
                "row_id",
                "source_row",
                "text_original",
                "text_proposed",
                "changed",
                "replacement_count",
                "applied_rules",
            ])
            change_writer = csv.DictWriter(change_file, fieldnames=[
                "row_id",
                "source_row",
                "rule_id",
                "occurrences",
            ])
            data_writer.writeheader()
            change_writer.writeheader()

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
                    occurrences = proposed.count(rule["damaged"])

                    if occurrences:
                        proposed = proposed.replace(
                            rule["damaged"], rule["replacement"]
                        )
                        counts[rule["rule_id"]] += occurrences
                        replacements += occurrences
                        applied.append(rule["rule_id"])

                        change_writer.writerow({
                            "row_id": row_id,
                            "source_row": index,
                            "rule_id": rule["rule_id"],
                            "occurrences": occurrences,
                        })

                is_changed = proposed != original
                changed += int(is_changed)

                data_writer.writerow({
                    "row_id": row_id,
                    "source_row": index,
                    "text_original": original,
                    "text_proposed": proposed,
                    "changed": int(is_changed),
                    "replacement_count": replacements,
                    "applied_rules": ";".join(applied),
                })

    # Verify row preservation against the source snapshot.
    with (
        (run_dir / "source_snapshot.csv").open(
            encoding="utf-8-sig", newline=""
        ) as original_file,
        dataset.open(encoding="utf-8-sig", newline="") as derived_file,
    ):
        originals = csv.DictReader(original_file)
        derived = csv.DictReader(derived_file)
        verified = 0

        for original in originals:
            output_row = next(derived, None)

            if output_row is None:
                raise RuntimeError("Derived dataset has missing rows")

            if original["text"] != output_row["text_original"]:
                raise RuntimeError("Original text preservation failed")

            verified += 1

        if next(derived, None) is not None:
            raise RuntimeError("Derived dataset has extra rows")

    if sha256(SOURCE) != source_hash:
        raise RuntimeError("Source changed during execution")

    report = {
        "run_id": run_id,
        "started_utc": started.isoformat(),
        "python_version": platform.python_version(),
        "source_sha256": source_hash,
        "rules_count": len(rules),
        "total_rows": total,
        "changed_rows": changed,
        "unchanged_rows": total - changed,
        "replacement_occurrences": sum(counts.values()),
        "occurrences_by_rule": counts,
        "verified_original_rows": verified,
        "source_modified": False,
        "rows_removed": 0,
        "status": "partial_encoding_repair_proposal",
        "all_encoding_defects_resolved": False,
        "normalization_applied": False,
        "labels_created": False,
    }

    (run_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    manifest = [
        {
            "file": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(run_dir.iterdir())
        if path.is_file()
    ]
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2))
    print("Experiment saved:", run_dir)


if __name__ == "__main__":
    main()