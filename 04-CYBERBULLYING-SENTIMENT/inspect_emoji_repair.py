import csv
import hashlib
import json
from pathlib import Path

INPUT = Path("data/raw/tweets_raw.csv")
OUTPUT = Path("results/emoji_repair_probe_restored.json")

FRAGMENTS = [
    "\u0623\u00b0\u0622\u06ba\u0622\u06a9\u0622\u0688",
    "\u0623\u00b0\u0622\u06ba\u0622\u06a9\u0622\u06a9",
    "\u0623\u00b0\u0622\u06ba\u0622\u06a9\u0622\u201a",
    "\u0623\u00b0\u0622\u06ba\u0622\u2122\u0622\u201e",
]

CODECS = ["cp1256", "cp1252", "latin1"]


def propose(fragment):
    candidates = []

    for first_codec in CODECS:
        try:
            intermediate = fragment.encode(first_codec).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue

        for second_codec in CODECS:
            try:
                repaired = intermediate.encode(second_codec).decode("utf-8")

                reconstructed = (
                    repaired.encode("utf-8")
                    .decode(second_codec)
                    .encode("utf-8")
                    .decode(first_codec)
                )

                if reconstructed == fragment:
                    candidates.append({
                        "first_codec": first_codec,
                        "second_codec": second_codec,
                        "proposed": repaired,
                        "codepoints": [
                            f"U+{ord(char):04X}" for char in repaired
                        ],
                        "roundtrip_verified": True,
                    })
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue

    return candidates


def main():
    source_hash = hashlib.sha256(INPUT.read_bytes()).hexdigest()
    counts = dict.fromkeys(FRAGMENTS, 0)

    with INPUT.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames != ["text"]:
            raise ValueError(f"Unexpected columns: {reader.fieldnames}")

        for index, row in enumerate(reader, start=1):
            text = row.get("text")

            if None in row or text is None:
                raise ValueError(f"Malformed record: {index}")

            for fragment in FRAGMENTS:
                counts[fragment] += text.count(fragment)

    report = {
        "source_sha256": source_hash,
        "source_modified": False,
        "repairs_applied": 0,
        "probes": [
            {
                "fragment": fragment,
                "occurrences": counts[fragment],
                "candidates": propose(fragment),
            }
            for fragment in FRAGMENTS
        ],
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    output = json.dumps(report, indent=2, ensure_ascii=True)
    OUTPUT.write_text(output, encoding="utf-8")
    print(output)
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()