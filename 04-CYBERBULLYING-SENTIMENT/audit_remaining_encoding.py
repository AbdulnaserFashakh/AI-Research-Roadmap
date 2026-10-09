import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from preview_encoding_repair import REPLACEMENTS

INPUT = Path("data/raw/tweets_raw.csv")
OUTPUT = Path("data/review/remaining_encoding_fragments.csv")
REPORT = Path("results/remaining_encoding_audit.json")

START_MARKERS = ("\u0623", "\u0622")
CODECS = ["cp1256", "cp1252", "latin1"]


def apply_current_rules(text):
    for damaged, replacement in REPLACEMENTS.items():
        text = text.replace(damaged, replacement)
    return text


def extract_fragments(text):
    """Extract consecutive non-ASCII runs starting at observed markers."""
    index = 0

    while index < len(text):
        if text[index] in START_MARKERS:
            end = index + 1

            while (
                end < len(text)
                and ord(text[end]) > 127
                and not text[end].isspace()
            ):
                end += 1

            fragment = text[index:end]

            if len(fragment) >= 2:
                yield fragment

            index = end
        else:
            index += 1


def decoding_candidates(fragment):
    candidates = []

    for first_codec in CODECS:
        try:
            intermediate = fragment.encode(first_codec).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue

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
                        "first_codec": first_codec,
                        "second_codec": second_codec,
                        "proposed": proposed,
                    })
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue

    return candidates


def main():
    counts = Counter()
    examples = {}
    total = 0
    flagged_rows = 0

    with INPUT.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames != ["text"]:
            raise ValueError(f"Unexpected columns: {reader.fieldnames}")

        for index, row in enumerate(reader, start=1):
            original = row.get("text")

            if None in row or original is None:
                raise ValueError(f"Malformed record: {index}")

            total += 1
            proposed = apply_current_rules(original)
            fragments = list(extract_fragments(proposed))

            if fragments:
                flagged_rows += 1

            for fragment in fragments:
                counts[fragment] += 1
                examples.setdefault(fragment, index)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "fragment",
                "fragment_escaped",
                "occurrences",
                "example_source_row",
                "decoding_candidates",
                "review_decision",
            ],
        )
        writer.writeheader()

        for fragment, occurrences in counts.most_common():
            writer.writerow({
                "fragment": fragment,
                "fragment_escaped": ascii(fragment),
                "occurrences": occurrences,
                "example_source_row": examples[fragment],
                "decoding_candidates": json.dumps(
                    decoding_candidates(fragment),
                    ensure_ascii=True,
                ),
                "review_decision": "",
            })

    report = {
        "source_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "rules_script_sha256": hashlib.sha256(
            Path("preview_encoding_repair.py").read_bytes()
        ).hexdigest(),
        "total_rows": total,
        "current_rules": len(REPLACEMENTS),
        "rows_with_remaining_candidate_fragments": flagged_rows,
        "distinct_candidate_fragments": len(counts),
        "candidate_fragment_occurrences": sum(counts.values()),
        "source_modified": False,
        "new_repairs_applied": 0,
        "limitation": (
            "Heuristic extraction may flag genuine Arabic text "
            "and may miss other encoding defects."
        ),
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    output = json.dumps(report, indent=2, ensure_ascii=True)
    REPORT.write_text(output, encoding="utf-8")
    print(output)

    print("\nTop 10 candidate fragments:")
    for fragment, occurrences in counts.most_common(10):
        print(json.dumps({
            "fragment": fragment,
            "occurrences": occurrences,
            "example_source_row": examples[fragment],
            "candidates": decoding_candidates(fragment),
        }, ensure_ascii=True))

    print("\nSaved:", OUTPUT)
    print("Saved:", REPORT)


if __name__ == "__main__":
    main()