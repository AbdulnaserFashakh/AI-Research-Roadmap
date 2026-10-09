import csv
import hashlib
import json
from pathlib import Path

INPUT = Path("data/review/remaining_encoding_fragments.csv")
OUTPUT = Path("data/review/remaining_encoding_candidates_v2.csv")
REPORT = Path("results/remaining_encoding_candidates_v2.json")

CODECS = ["cp1256", "cp1252", "latin1"]


def decoding_candidates(fragment):
    candidates = []

    for first_codec in CODECS:
        try:
            intermediate = fragment.encode(first_codec).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue

        reconstructed = intermediate.encode("utf-8").decode(first_codec)

        if reconstructed == fragment and intermediate != fragment:
            candidates.append({
                "stages": 1,
                "codecs": [first_codec],
                "proposed": intermediate,
                "roundtrip_verified": True,
            })

        for second_codec in CODECS:
            try:
                proposed = intermediate.encode(second_codec).decode("utf-8")
                reconstructed = (
                    proposed.encode("utf-8")
                    .decode(second_codec)
                    .encode("utf-8")
                    .decode(first_codec)
                )

                if reconstructed == fragment and proposed != fragment:
                    candidates.append({
                        "stages": 2,
                        "codecs": [first_codec, second_codec],
                        "proposed": proposed,
                        "roundtrip_verified": True,
                    })
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue

    return candidates


def main():
    total = 0
    no_candidate = 0
    one_output = 0
    multiple_outputs = 0
    examples = []

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with INPUT.open(encoding="utf-8-sig", newline="") as source:
        with OUTPUT.open(
            "w", encoding="utf-8-sig", newline=""
        ) as target:
            reader = csv.DictReader(source)
            fields = [
                "fragment",
                "occurrences",
                "example_source_row",
                "distinct_proposed_outputs",
                "decoding_candidates",
                "review_decision",
            ]
            writer = csv.DictWriter(target, fieldnames=fields)
            writer.writeheader()

            for row in reader:
                fragment = row["fragment"]
                candidates = decoding_candidates(fragment)
                outputs = {item["proposed"] for item in candidates}
                total += 1

                if not outputs:
                    no_candidate += 1
                elif len(outputs) == 1:
                    one_output += 1
                else:
                    multiple_outputs += 1

                writer.writerow({
                    "fragment": fragment,
                    "occurrences": row["occurrences"],
                    "example_source_row": row["example_source_row"],
                    "distinct_proposed_outputs": len(outputs),
                    "decoding_candidates": json.dumps(
                        candidates, ensure_ascii=True
                    ),
                    "review_decision": "",
                })

                if len(examples) < 10:
                    examples.append({
                        "fragment": fragment,
                        "occurrences": int(row["occurrences"]),
                        "candidates": candidates,
                    })

    report = {
        "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
        "distinct_fragments_tested": total,
        "fragments_without_candidates": no_candidate,
        "fragments_with_one_distinct_output": one_output,
        "fragments_with_multiple_distinct_outputs": multiple_outputs,
        "source_modified": False,
        "repairs_applied": 0,
        "status": "decoding_candidates_only",
        "limitation": (
            "Reversible decoding does not prove intended text. "
            "One-stage outputs may still contain encoding damage."
        ),
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2, ensure_ascii=True))
    print("\nFirst 10 fragment results:")
    for example in examples:
        print(json.dumps(example, ensure_ascii=True))

    print("\nSaved:", OUTPUT)
    print("Saved:", REPORT)


if __name__ == "__main__":
    main()