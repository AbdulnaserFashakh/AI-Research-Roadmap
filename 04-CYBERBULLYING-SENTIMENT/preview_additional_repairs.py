import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

INPUT = Path(
    "experiments/"
    "encoding_dataset_v1_20261009T184159656645Z/"
    "dataset_proposed.csv"
)

# Exact candidates inspected in contextual previews.
# These remain proposals, not globally validated repairs.
RULES = {
    "\u0623\u00a2\u0622\u20ac\u0622\u06a9": "\u2018",
    "\u0623\u00a9": "\u00e9",
    "\u0623\u00a2\u0622\u20ac\u0622\u00a2": "\u2022",
    "\u0623\u00a3": "\u00e3",
    "\u0623\u00b0\u0622\u06ba\u0622\u06a9\u0622\u00ad": "\U0001F62D",
    "\u0623\u060c": "\u00e1",
    "\u0623\u00a2\u0622\u2014\u0622\u2014": "\u25d7",
    "\u0623\u00ad": "\u00ed",
    "\u0623\u00b0\u0622\u06ba\u0622\u06a9\u0622\u00a9": "\U0001F629",
    "\u0623\u00a2\u0622\u2014\u0622\u2013": "\u25d6",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    run_id = datetime.now(timezone.utc).strftime(
        "additional_repairs_%Y%m%dT%H%M%S%fZ"
    )
    folder = Path("experiments") / run_id
    folder.mkdir(parents=True, exist_ok=False)

    input_hash = sha256(INPUT)
    shutil.copy2(INPUT, folder / "input_snapshot.csv")
    shutil.copy2(Path(__file__), folder / Path(__file__).name)

    if sha256(folder / "input_snapshot.csv") != input_hash:
        raise RuntimeError("Input snapshot checksum mismatch")

    counts = dict.fromkeys(RULES, 0)
    total = changed = 0
    output = folder / "additional_repair_preview.csv"

    with INPUT.open(encoding="utf-8-sig", newline="") as source:
        with output.open("w", encoding="utf-8-sig", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=[
                "row_id",
                "source_row",
                "text_before",
                "text_after",
                "replacement_count",
                "review_decision",
            ])
            writer.writeheader()

            for row in csv.DictReader(source):
                total += 1
                before = row["text_proposed"]
                after = before
                replacements = 0

                for damaged, replacement in RULES.items():
                    occurrences = after.count(damaged)
                    counts[damaged] += occurrences
                    replacements += occurrences
                    after = after.replace(damaged, replacement)

                if after != before:
                    changed += 1
                    writer.writerow({
                        "row_id": row["row_id"],
                        "source_row": row["source_row"],
                        "text_before": before,
                        "text_after": after,
                        "replacement_count": replacements,
                        "review_decision": "",
                    })

    if sha256(INPUT) != input_hash:
        raise RuntimeError("Input changed during execution")

    report = {
        "run_id": run_id,
        "input_sha256": input_hash,
        "total_rows": total,
        "rows_with_additional_proposals": changed,
        "replacement_occurrences": sum(counts.values()),
        "rules": [
            {
                "damaged": damaged,
                "replacement": replacement,
                "occurrences": counts[damaged],
            }
            for damaged, replacement in RULES.items()
        ],
        "input_modified": False,
        "status": "additional_proposals_for_review",
        "output_contains": "changed_rows_only",
    }

    (folder / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    manifest = [
        {
            "file": path.name,
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(folder.iterdir())
        if path.is_file()
    ]
    (folder / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2, ensure_ascii=True))
    print("Experiment saved:", folder)


if __name__ == "__main__":
    main()