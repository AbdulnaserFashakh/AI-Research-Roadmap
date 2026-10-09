import csv
import json
from pathlib import Path

INPUT = Path("data/raw/tweets_raw.csv")
OUTPUT = Path("results/raw_encoding_check.json")
SELECTED_ROWS = {4186, 56335, 6436}


def main():
    records = []

    with INPUT.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for index, row in enumerate(reader, start=1):
            if index in SELECTED_ROWS:
                records.append({
                    "source_row": index,
                    "text": row["text"],
                })

    report = {
        "input_file": INPUT.as_posix(),
        "matched_rows": len(records),
        "records": records,
        "source_modified": False,
    }

    output = json.dumps(report, indent=2, ensure_ascii=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()