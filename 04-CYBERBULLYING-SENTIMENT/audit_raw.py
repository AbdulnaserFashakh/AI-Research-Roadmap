import csv
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

INPUT = Path("data/raw/tweets_raw.csv")
OUTPUT = Path("results/raw_audit.json")


def main():
    source_hash = hashlib.sha256(INPUT.read_bytes()).hexdigest()
    total = 0
    empty = 0
    seen = set()
    duplicates = 0

    with INPUT.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames != ["text"]:
            raise ValueError(
                f"Expected one column named text. Found {reader.fieldnames}"
            )

        for row_number, row in enumerate(reader, start=2):
            if None in row or row.get("text") is None:
                raise ValueError(f"Malformed CSV record at record {row_number}")

            text = row["text"]
            total += 1

            if not text.strip():
                empty += 1
                continue

            if text in seen:
                duplicates += 1
            else:
                seen.add(text)

    report = {
        "input_file": INPUT.as_posix(),
        "source_sha256": source_hash,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "total_rows": total,
        "empty_tweets": empty,
        "nonempty_tweets": total - empty,
        "unique_nonempty_texts_exact": len(seen),
        "duplicate_excess_rows_exact": duplicates,
        "source_modified": False,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nSaved to {OUTPUT}")


if __name__ == "__main__":
    main()