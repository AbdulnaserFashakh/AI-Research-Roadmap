import csv
import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from audit_remaining_encoding import extract_fragments
from preview_additional_repairs import RULES

INPUT = Path(
    "experiments/"
    "encoding_dataset_v1_20261009T184159656645Z/"
    "dataset_proposed.csv"
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    run_id = datetime.now(timezone.utc).strftime(
        "repair_boundaries_%Y%m%dT%H%M%S%fZ"
    )
    folder = Path("experiments") / run_id
    folder.mkdir(parents=True, exist_ok=False)

    input_hash = sha256(INPUT)

    for script in [
        Path(__file__),
        Path("audit_remaining_encoding.py"),
        Path("preview_additional_repairs.py"),
        Path("preview_encoding_repair.py"),
    ]:
        shutil.copy2(script, folder / script.name)

    shutil.copy2(INPUT, folder / "input_snapshot.csv")
    if sha256(folder / "input_snapshot.csv") != input_hash:
        raise RuntimeError("Input snapshot checksum mismatch")

    counts = Counter()
    seen_examples = set()
    total = 0
    output = folder / "boundary_review.csv"

    with INPUT.open(encoding="utf-8-sig", newline="") as source:
        with output.open("w", encoding="utf-8-sig", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=[
                "row_id",
                "source_row",
                "damaged_rule",
                "replacement",
                "containing_fragment",
                "match_type",
                "occurrences",
                "text_before",
                "text_after_this_rule",
                "review_decision",
            ])
            writer.writeheader()

            for row in csv.DictReader(source):
                total += 1
                text = row["text_proposed"]

                for fragment in extract_fragments(text):
                    for damaged, replacement in RULES.items():
                        occurrences = fragment.count(damaged)
                        if not occurrences:
                            continue

                        match_type = (
                            "whole_extracted_fragment"
                            if fragment == damaged
                            else "inside_longer_fragment"
                        )
                        counts[match_type] += occurrences

                        key = (damaged, fragment)
                        if key in seen_examples:
                            continue
                        seen_examples.add(key)

                        writer.writerow({
                            "row_id": row["row_id"],
                            "source_row": row["source_row"],
                            "damaged_rule": damaged,
                            "replacement": replacement,
                            "containing_fragment": fragment,
                            "match_type": match_type,
                            "occurrences": occurrences,
                            "text_before": text,
                            "text_after_this_rule": text.replace(
                                damaged, replacement
                            ),
                            "review_decision": "",
                        })

    if sha256(INPUT) != input_hash:
        raise RuntimeError("Input changed during execution")

    report = {
        "run_id": run_id,
        "input_sha256": input_hash,
        "total_rows": total,
        "match_occurrences_by_type": dict(counts),
        "distinct_rule_fragment_pairs": len(seen_examples),
        "input_modified": False,
        "repairs_applied": 0,
        "limitation": (
            "Fragment boundaries are heuristic. "
            "Matches inside longer fragments are not necessarily wrong. "
            "Preview applies one rule at a time."
        ),
    }

    (folder / "report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

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

    print(json.dumps(report, indent=2))
    print("Experiment saved:", folder)

    print("\nFirst 5 longer-fragment examples:")
    shown = 0
    with output.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            if row["match_type"] == "inside_longer_fragment":
                print(json.dumps({
                    "source_row": row["source_row"],
                    "damaged_rule": row["damaged_rule"],
                    "replacement": row["replacement"],
                    "containing_fragment": row["containing_fragment"],
                    "text_after_this_rule": row["text_after_this_rule"],
                }, ensure_ascii=True))
                shown += 1
                if shown == 5:
                    break


if __name__ == "__main__":
    main()