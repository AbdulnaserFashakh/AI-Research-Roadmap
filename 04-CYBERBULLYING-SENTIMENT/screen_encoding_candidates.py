import csv
import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path

INPUT = Path("data/review/remaining_encoding_candidates_v2.csv")
SOURCE = Path("data/raw/tweets_raw.csv")
OUTPUT = Path("data/review/encoding_candidates_screened.csv")
REPORT = Path("results/encoding_candidates_screened.json")


def exclusion_reasons(text):
    reasons = []

    if any(unicodedata.category(char).startswith("C") for char in text):
        reasons.append("control_or_format_character")

    if "\ufffd" in text:
        reasons.append("replacement_character")

    if "\u0623" in text or "\u0622" in text:
        reasons.append("observed_marker_remains")

    return reasons


def main():
    # Load source texts for contextual review.
    source_texts = {}

    with SOURCE.open(encoding="utf-8-sig", newline="") as file:
        for index, row in enumerate(csv.DictReader(file), start=1):
            source_texts[index] = row["text"]

    counts = Counter()
    examples = []

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with INPUT.open(encoding="utf-8-sig", newline="") as source:
        with OUTPUT.open(
            "w", encoding="utf-8-sig", newline=""
        ) as target:
            reader = csv.DictReader(source)
            writer = csv.DictWriter(target, fieldnames=[
                "fragment",
                "occurrences",
                "example_source_row",
                "screening_status",
                "remaining_outputs",
                "excluded_candidates",
                "context_original",
                "context_proposed",
                "review_decision",
            ])
            writer.writeheader()

            for row in reader:
                fragment = row["fragment"]
                candidates = json.loads(row["decoding_candidates"])
                remaining = set()
                excluded = []

                for candidate in candidates:
                    proposed = candidate["proposed"]
                    reasons = exclusion_reasons(proposed)

                    if reasons:
                        excluded.append({
                            "proposed": proposed,
                            "reasons": reasons,
                        })
                    else:
                        remaining.add(proposed)

                if not candidates:
                    status = "no_decoding_candidate"
                elif not remaining:
                    status = "all_candidates_excluded_by_heuristic"
                elif len(remaining) == 1:
                    status = "one_candidate_for_context_review"
                else:
                    status = "multiple_candidates_for_context_review"

                counts[status] += 1
                source_row = int(row["example_source_row"])
                context = source_texts[source_row]

                proposed_context = ""
                if len(remaining) == 1:
                    replacement = next(iter(remaining))
                    proposed_context = context.replace(
                        fragment, replacement
                    )

                writer.writerow({
                    "fragment": fragment,
                    "occurrences": row["occurrences"],
                    "example_source_row": source_row,
                    "screening_status": status,
                    "remaining_outputs": json.dumps(
                        sorted(remaining), ensure_ascii=True
                    ),
                    "excluded_candidates": json.dumps(
                        excluded, ensure_ascii=True
                    ),
                    "context_original": context,
                    "context_proposed": proposed_context,
                    "review_decision": "",
                })

                if len(examples) < 10:
                    examples.append({
                        "fragment": fragment,
                        "status": status,
                        "remaining_outputs": sorted(remaining),
                        "context_original": context,
                        "context_proposed": proposed_context,
                    })

    report = {
        "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
        "fragment_status_counts": dict(counts),
        "source_modified": False,
        "repairs_applied": 0,
        "limitation": (
            "Heuristic screening is not repair validation. "
            "Legitimate format characters or Arabic may be excluded. "
            "Context preview uses exact fragment replacement only."
        ),
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps(report, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2, ensure_ascii=True))

    print("\nFirst 10 contextual previews:")
    for example in examples:
        print(json.dumps(example, ensure_ascii=True))

    print("\nSaved:", OUTPUT)
    print("Saved:", REPORT)


if __name__ == "__main__":
    main()