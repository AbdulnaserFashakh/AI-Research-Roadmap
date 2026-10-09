import csv
import hashlib
import io
import json
from pathlib import Path

FILES = {
    "original": Path("data/raw/tweets_original.csv"),
    "working": Path("data/raw/tweets_raw.csv"),
}
SELECTED_ROWS = {4186, 6436, 56335}
OUTPUT = Path("results/encoding_comparison.json")


def inspect(path):
    raw = path.read_bytes()

    try:
        decoded = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        return {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "utf8_valid": False,
            "error_byte_position": error.start,
            "records": [],
        }

    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    columns = reader.fieldnames
    records = []
    total = 0

    if "text" not in (columns or []):
        raise ValueError(f"{path}: text column missing. Found {columns}")

    for index, row in enumerate(reader, start=1):
        total += 1
        if index in SELECTED_ROWS:
            records.append({
                "source_row": index,
                "text": row["text"],
            })

    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "utf8_valid": True,
        "columns": columns,
        "total_rows": total,
        "records": records,
    }


def main():
    report = {
        name: inspect(path)
        for name, path in FILES.items()
    }
    def read_texts(path):
        with path.open(encoding="utf-8-sig", newline="") as file:
            return [row["text"] for row in csv.DictReader(file)]

    original = read_texts(FILES["original"])
    working = read_texts(FILES["working"])

    mismatches = [
        index
        for index, (first, second) in enumerate(
            zip(original, working), start=1
        )
        if first != second
    ]

    report["full_text_comparison"] = {
        "same_row_count": len(original) == len(working),
        "same_text_and_order": original == working,
        "different_paired_rows": len(mismatches),
        "first_different_rows": mismatches[:10],
    }
    # Matching row numbers alone does not prove matching source records.
    report["source_files_modified"] = False
    output = json.dumps(report, indent=2, ensure_ascii=True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()