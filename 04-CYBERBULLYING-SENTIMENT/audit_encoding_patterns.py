import csv
import hashlib
import json
from pathlib import Path

INPUT = Path("data/raw/tweets_raw.csv")
REPORT = Path("results/encoding_patterns.json")
REVIEW = Path("data/review/encoding_candidates.csv")

# Patterns observed in the inspected tweets.
# Matches are candidates for review, not proof of corruption.
PATTERNS = {
    "double_encoded_sequence": "\u0623\u00a2\u0622",
    "encoded_accent_sequence": "\u0623\u00a3",
    "replacement_character": "\ufffd",
}


def main():
    counts = {name: 0 for name in PATTERNS}
    candidates = []
    total = 0

    with INPUT.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames != ["text"]:
            raise ValueError(f"Unexpected columns: {reader.fieldnames}")

        for index, row in enumerate(reader, start=1):
            text = row.get("text")

            if None in row or text is None:
                raise ValueError(f"Malformed record: {index}")

            total += 1
            matches = [
                name
                for name, pattern in PATTERNS.items()
                if pattern in text
            ]

            for name in matches:
                counts[name] += 1

            if matches:
                candidates.append({
                    "source_row": index,
                    "text_original": text,
                    "matched_patterns": ";".join(matches),
                })

    REVIEW.parent.mkdir(parents=True, exist_ok=True)

    with REVIEW.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "source_row",
                "text_original",
                "matched_patterns",
            ],
        )
        writer.writeheader()
        writer.writerows(candidates)

    report = {
        "source_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "total_rows": total,
        "candidate_rows": len(candidates),
        "rows_matching_each_pattern": counts,
        "patterns_unicode": PATTERNS,
        "source_modified": False,
        "repairs_applied": 0,
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    output = json.dumps(report, indent=2, ensure_ascii=True)
    REPORT.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()