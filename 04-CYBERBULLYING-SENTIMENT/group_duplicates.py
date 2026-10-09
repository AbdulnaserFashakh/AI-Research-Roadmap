import csv
import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path

INPUT = Path("data/raw/tweets_raw.csv")
OUTPUT = Path("data/processed/tweets_grouped.csv")
REPORT = Path("results/duplicate_groups.json")


def normalize_for_grouping(text):
    text = unicodedata.normalize("NFKC", text)
    return " ".join(text.casefold().split())


def main():
    source_hash = hashlib.sha256(INPUT.read_bytes()).hexdigest()
    rows = []
    counts = Counter()

    with INPUT.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames != ["text"]:
            raise ValueError(f"Unexpected columns: {reader.fieldnames}")

        for index, row in enumerate(reader, start=1):
            text = row.get("text")
            if None in row or text is None:
                raise ValueError(f"Malformed record: {index}")
            if not text.strip():
                raise ValueError(f"Empty tweet: {index}")

            normalized = normalize_for_grouping(text)
            group_id = hashlib.sha256(
                normalized.encode("utf-8")
            ).hexdigest()

            rows.append({
                "row_id": f"{source_hash[:16]}_{index:06d}",
                "text": text,
                "group_id": group_id,
            })
            counts[group_id] += 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as file:
        fields = ["row_id", "text", "group_id", "group_size"]
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for row in rows:
            writer.writerow({
                **row,
                "group_size": counts[row["group_id"]],
            })

    report = {
        "source_sha256": source_hash,
        "total_rows": len(rows),
        "normalized_groups": len(counts),
        "duplicate_excess_rows": len(rows) - len(counts),
        "groups_with_multiple_rows": sum(
            size > 1 for size in counts.values()
        ),
        "largest_group_size": max(counts.values(), default=0),
        "normalization": "NFKC + casefold + whitespace collapse",
        "original_text_preserved": True,
        "rows_removed": 0,
        "near_duplicates_checked": False,
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()