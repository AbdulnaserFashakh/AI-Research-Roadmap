import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from audit_remaining_encoding_v2 import decoding_candidates

PREVIOUS_RUN = Path(
    "experiments/encoding_dataset_v2_20261009T192006935492Z"
)
FRAGMENTS = PREVIOUS_RUN / "remaining_fragments.csv"
DATASET = PREVIOUS_RUN / "dataset_proposed.csv"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    run_id = datetime.now(timezone.utc).strftime(
        "remaining_top10_%Y%m%dT%H%M%S%fZ"
    )
    folder = Path("experiments") / run_id
    folder.mkdir(parents=True, exist_ok=False)

    with FRAGMENTS.open(encoding="utf-8-sig", newline="") as file:
        selected = list(csv.DictReader(file))[:10]

    required_rows = {
        int(row["example_source_row"]) for row in selected
    }
    contexts = {}

    with DATASET.open(encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            index = int(row["source_row"])
            if index in required_rows:
                contexts[index] = row["text_proposed"]

    probes = []

    for row in selected:
        fragment = row["fragment"]
        index = int(row["example_source_row"])
        context = contexts[index]
        candidates = decoding_candidates(fragment)

        for candidate in candidates:
            candidate["codepoints"] = [
                f"U+{ord(char):04X}"
                for char in candidate["proposed"]
            ]
            candidate["context_proposed"] = context.replace(
                fragment, candidate["proposed"]
            )

        probes.append({
            "fragment": fragment,
            "occurrences": int(row["occurrences"]),
            "example_source_row": index,
            "context_before": context,
            "candidates": candidates,
        })

    report = {
        "run_id": run_id,
        "fragment_file_sha256": sha256(FRAGMENTS),
        "dataset_sha256": sha256(DATASET),
        "repairs_applied": 0,
        "source_modified": False,
        "status": "contextual_decoding_probe",
        "probes": probes,
    }

    for path in [
        Path(__file__),
        Path("audit_remaining_encoding_v2.py"),
        FRAGMENTS,
    ]:
        shutil.copy2(path, folder / path.name)

    output = folder / "report.json"
    output.write_text(
        json.dumps(report, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    manifest = [
        {
            "file": path.name,
            "sha256": sha256(path),
        }
        for path in sorted(folder.iterdir())
        if path.is_file()
    ]
    (folder / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    entry = (
        f"\n\n## Remaining-fragment probe — {run_id}\n"
        "- Script: probe_remaining_top10.py\n"
        "- Examined the ten most frequent remaining fragments.\n"
        "- Tested reversible one-stage and two-stage decoding.\n"
        "- Preserved contextual previews and code in the experiment.\n"
        "- Input dataset identified by SHA-256 in report.json.\n"
        "- No repairs applied. Candidates require contextual review.\n"
    )
    (folder / "methods_entry.md").write_text(entry, encoding="utf-8")

    with Path("METHODS_LOG.md").open("a", encoding="utf-8") as file:
        file.write(entry)

    print(json.dumps(report, indent=2, ensure_ascii=True))
    print("Experiment saved:", folder)


if __name__ == "__main__":
    main()