import csv
import hashlib
import json
from pathlib import Path

INPUT = Path("data/raw/tweets_raw.csv")
OUTPUT = Path("data/review/encoding_repair_preview.csv")
REPORT = Path("results/encoding_repair_preview.json")

REPLACEMENTS = {
    # Punctuation
    "\u0623\u00a2\u0622\u20ac\u0622\u2122": "\u2019",
    "\u0623\u00a2\u0622\u20ac\u0622\u0153": "\u201c",
    "\u0623\u00a2\u0622\u20ac\u0622\u200c": "\u201d",
    "\u0623\u00a2\u0622\u20ac\u0622\u201d": "\u2014",
    "\u0623\u00a2\u0622\u20ac\u0622\u00a6": "\u2026",

    # Emoji fragments with verified reversible decoding
    "\u0623\u00b0\u0622\u06ba\u0622\u06a9\u0622\u0688": "\U0001F60F",
    "\u0623\u00b0\u0622\u06ba\u0622\u06a9\u0622\u06a9": "\U0001F618",
    "\u0623\u00b0\u0622\u06ba\u0622\u06a9\u0622\u201a": "\U0001F602",
    "\u0623\u00b0\u0622\u06ba\u0622\u2122\u0622\u201e": "\U0001F644",
}


def main():
    source_hash = hashlib.sha256(INPUT.read_bytes()).hexdigest()
    total = 0
    changed = 0
    shown = set()
    rule_counts = dict.fromkeys(REPLACEMENTS, 0)

    fields = [
        "source_row",
        "text_original",
        "text_proposed",
        "replacement_count",
        "review_decision",
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with INPUT.open(encoding="utf-8-sig", newline="") as source:
        with OUTPUT.open(
            "w", encoding="utf-8-sig", newline=""
        ) as target:
            reader = csv.DictReader(source)

            if reader.fieldnames != ["text"]:
                raise ValueError(
                    f"Expected one text column. Found {reader.fieldnames}"
                )

            writer = csv.DictWriter(target, fieldnames=fields)
            writer.writeheader()

            for index, row in enumerate(reader, start=1):
                original = row.get("text")

                if None in row or original is None:
                    raise ValueError(f"Malformed record: {index}")

                total += 1
                proposed = original
                count = 0

                for damaged, replacement in REPLACEMENTS.items():
                    occurrences = proposed.count(damaged)
                    rule_counts[damaged] += occurrences
                    count += occurrences
                    proposed = proposed.replace(damaged, replacement)

                for damaged, replacement in REPLACEMENTS.items():
                    if damaged in original and damaged not in shown:
                        shown.add(damaged)
                        print(
                            "\nRule:",
                            ascii(damaged),
                            "->",
                            ascii(replacement),
                        )
                        print("Source row:", index)
                        print("Before:", ascii(original))
                        print("After:", ascii(proposed))

                if proposed != original:
                    changed += 1
                    writer.writerow({
                        "source_row": index,
                        "text_original": original,
                        "text_proposed": proposed,
                        "replacement_count": count,
                        "review_decision": "",
                    })

    if hashlib.sha256(INPUT.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError("Source file changed during execution")

    report = {
        "source_sha256": source_hash,
        "total_rows": total,
        "rows_with_proposed_changes": changed,
        "total_replacement_occurrences": sum(rule_counts.values()),
        "rules": [
            {
                "damaged": damaged,
                "replacement": replacement,
                "occurrences": rule_counts[damaged],
            }
            for damaged, replacement in REPLACEMENTS.items()
        ],
        "source_modified": False,
        "status": "proposals_for_review",
        "output_contains": "changed_rows_only",
        "all_encoding_defects_resolved": False,
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    print("\nTotal rows:", total)
    print("Rows with proposed changes:", changed)
    print("Replacement occurrences:", sum(rule_counts.values()))
    print("Preview saved:", OUTPUT)
    print("Report saved:", REPORT)
    print("Source unchanged. Proposals require review.")


if __name__ == "__main__":
    main()