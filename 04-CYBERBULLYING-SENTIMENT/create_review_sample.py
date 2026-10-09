import csv
import hashlib
import json
import random
from pathlib import Path

INPUT = Path("data/processed/tweets_grouped.csv")
OUTPUT = Path("data/review/pilot_100.csv")
MANIFEST = Path("results/pilot_100_manifest.json")
SEED = 42
SAMPLE_SIZE = 100


def main():
    representatives = {}

    with INPUT.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            representatives.setdefault(row["group_id"], row)

    groups = sorted(representatives)

    if len(groups) < SAMPLE_SIZE:
        raise ValueError("Not enough groups for the requested sample")

    selected = random.Random(SEED).sample(groups, SAMPLE_SIZE)

    fields = [
        "row_id",
        "text",
        "group_id",
        "abuse_label",
        "mentioned_groups",
        "targeted_groups",
        "sentiment",
        "uncertain",
        "rationale",
        "annotator_id",
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT.exists():
        raise FileExistsError(
            f"{OUTPUT} already exists. Preserve completed annotations."
        )

    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()

        for group_id in selected:
            row = representatives[group_id]
            writer.writerow({
                "row_id": row["row_id"],
                "text": row["text"],
                "group_id": group_id,
            })

    manifest = {
        "input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "output_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "seed": SEED,
        "sample_size": SAMPLE_SIZE,
        "sampling_unit": "normalized text group",
        "available_groups": len(groups),
        "representative": "first source row within each group",
        "purpose": "annotation guideline pilot, not evaluation",
        "labels": "blank for human review",
        "selected_group_ids": selected,
    }

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print(f"Saved {SAMPLE_SIZE} texts to {OUTPUT}")
    print(f"Saved sampling record to {MANIFEST}")


if __name__ == "__main__":
    main()