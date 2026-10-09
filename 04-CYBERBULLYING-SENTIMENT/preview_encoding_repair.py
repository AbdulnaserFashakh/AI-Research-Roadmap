import csv
from pathlib import Path

INPUT = Path("data/review/encoding_candidates.csv")
OUTPUT = Path("data/review/encoding_repair_preview.csv")

REPLACEMENTS = {
    "\u0623\u00a2\u0622\u20ac\u0622\u2122": "\u2019",
    "\u0623\u00a2\u0622\u20ac\u0622\u0153": "\u201c",
    "\u0623\u00a2\u0622\u20ac\u0622\u200c": "\u201d",
    "\u0623\u00a2\u0622\u20ac\u0622\u201d": "\u2014",
    "\u0623\u00a2\u0622\u20ac\u0622\u00a6": "\u2026",
}


def main():
    changed = 0
    shown = set()
    fields = [
        "source_row",
        "text_original",
        "text_proposed",
        "replacement_count",
        "review_decision",
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with INPUT.open(encoding="utf-8-sig", newline="") as source:
        with OUTPUT.open("w", encoding="utf-8-sig", newline="") as target:
            reader = csv.DictReader(source)
            writer = csv.DictWriter(target, fieldnames=fields)
            writer.writeheader()

            for row in reader:
                original = row["text_original"]
                proposed = original
                count = 0

                for damaged, replacement in REPLACEMENTS.items():
                    count += proposed.count(damaged)
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
                        print("Source row:", row["source_row"])
                        print("Before:", ascii(original))
                        print("After:", ascii(proposed))
                if proposed != original:
                    changed += 1
                    writer.writerow({
                        "source_row": row["source_row"],
                        "text_original": original,
                        "text_proposed": proposed,
                        "replacement_count": count,
                        "review_decision": "",
                    })

    print("Rows with proposed changes:", changed)
    print("Saved:", OUTPUT)
    print("Source unchanged. Proposals require review.")


if __name__ == "__main__":
    main()