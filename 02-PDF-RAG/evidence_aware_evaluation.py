from pathlib import Path
import json


project_folder = Path(__file__).parent

questions_path = (
    project_folder / "evaluation_questions.json"
)

dense_candidates_path = (
    project_folder
    / "retrieval_candidates_k5_baseline.json"
)

reranked_candidates_path = (
    project_folder
    / "retrieval_candidates_dense20_reranked.json"
)

output_path = (
    project_folder
    / "evidence_aware_metrics_dense_vs_reranked.json"
)

final_k = 5


def load_json(path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def evaluate_evidence(
    retrieved_chunk_ids,
    evidence_groups
):
    retrieved_set = set(retrieved_chunk_ids)

    group_results = []

    for group in evidence_groups:
        acceptable_ids = set(
            group["acceptable_chunk_ids"]
        )

        matched_ids = sorted(
            retrieved_set.intersection(
                acceptable_ids
            )
        )

        group_results.append(
            {
                "claim_id": group["claim_id"],
                "claim": group["claim"],
                "acceptable_chunk_ids": sorted(
                    acceptable_ids
                ),
                "matched_chunk_ids": matched_ids,
                "covered": bool(matched_ids)
            }
        )

    covered_count = sum(
        1
        for group in group_results
        if group["covered"]
    )

    total_count = len(group_results)

    coverage = (
        covered_count / total_count
        if total_count
        else 0.0
    )

    return {
        "retrieved_chunk_ids": (
            retrieved_chunk_ids
        ),
        "covered_claims": covered_count,
        "total_claims": total_count,
        "claim_coverage": round(
            coverage,
            4
        ),
        "complete_evidence": (
            1.0
            if covered_count == total_count
            else 0.0
        ),
        "any_evidence": (
            1.0
            if covered_count > 0
            else 0.0
        ),
        "claim_results": group_results
    }


def summarize(per_question, method_name):
    question_count = len(per_question)

    total_claims = sum(
        item[method_name]["total_claims"]
        for item in per_question
    )

    covered_claims = sum(
        item[method_name]["covered_claims"]
        for item in per_question
    )

    macro_coverage = sum(
        item[method_name]["claim_coverage"]
        for item in per_question
    ) / question_count

    micro_coverage = (
        covered_claims / total_claims
    )

    complete_rate = sum(
        item[method_name]["complete_evidence"]
        for item in per_question
    ) / question_count

    any_evidence_rate = sum(
        item[method_name]["any_evidence"]
        for item in per_question
    ) / question_count

    return {
        "questions": question_count,
        "covered_claims": covered_claims,
        "total_claims": total_claims,
        "macro_claim_coverage": round(
            macro_coverage,
            4
        ),
        "micro_claim_coverage": round(
            micro_coverage,
            4
        ),
        "complete_evidence_rate": round(
            complete_rate,
            4
        ),
        "any_evidence_rate": round(
            any_evidence_rate,
            4
        )
    }


questions = load_json(questions_path)

dense_results = load_json(
    dense_candidates_path
)

reranked_results = load_json(
    reranked_candidates_path
)


dense_by_id = {
    item["id"]: item
    for item in dense_results
}

reranked_by_id = {
    item["id"]: item
    for item in reranked_results
}


answerable_questions = [
    question
    for question in questions
    if question.get("answerable", True)
]


per_question = []

for question in answerable_questions:
    question_id = question["id"]

    evidence_groups = question.get(
        "evidence_groups",
        []
    )

    if not evidence_groups:
        raise ValueError(
            "Missing evidence groups for "
            f"{question_id}"
        )

    if question_id not in dense_by_id:
        raise ValueError(
            "Missing dense results for "
            f"{question_id}"
        )

    if question_id not in reranked_by_id:
        raise ValueError(
            "Missing reranked results for "
            f"{question_id}"
        )

    dense_chunk_ids = [
        candidate["chunk_id"]
        for candidate in dense_by_id[
            question_id
        ]["candidates"][:final_k]
    ]

    reranked_chunk_ids = [
        candidate["chunk_id"]
        for candidate in reranked_by_id[
            question_id
        ]["reranked_candidates"][:final_k]
    ]

    dense_evaluation = evaluate_evidence(
        dense_chunk_ids,
        evidence_groups
    )

    reranked_evaluation = evaluate_evidence(
        reranked_chunk_ids,
        evidence_groups
    )

    per_question.append(
        {
            "id": question_id,
            "dense_top5": dense_evaluation,
            "reranked_top5": (
                reranked_evaluation
            ),
            "coverage_delta": round(
                reranked_evaluation[
                    "claim_coverage"
                ]
                - dense_evaluation[
                    "claim_coverage"
                ],
                4
            )
        }
    )


dense_summary = summarize(
    per_question,
    "dense_top5"
)

reranked_summary = summarize(
    per_question,
    "reranked_top5"
)


metric_names = [
    "macro_claim_coverage",
    "micro_claim_coverage",
    "complete_evidence_rate",
    "any_evidence_rate"
]

delta = {
    metric: round(
        reranked_summary[metric]
        - dense_summary[metric],
        4
    )
    for metric in metric_names
}


report = {
    "configuration": {
        "final_k": final_k,
        "answerable_questions": len(
            answerable_questions
        ),
        "total_evidence_groups": sum(
            len(question["evidence_groups"])
            for question in answerable_questions
        ),
        "dense_candidates_file": (
            dense_candidates_path.name
        ),
        "reranked_candidates_file": (
            reranked_candidates_path.name
        )
    },
    "comparison": {
        "dense_top5": dense_summary,
        "reranked_top5": reranked_summary,
        "delta": delta
    },
    "per_question": per_question
}


output_path.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)


print("\nEVIDENCE-AWARE COMPARISON")

print(
    f"{'Metric':<25} | "
    f"{'Dense@5':>8} | "
    f"{'Reranked@5':>10} | "
    f"{'Delta':>8}"
)

print("-" * 62)

labels = {
    "macro_claim_coverage": (
        "Macro Claim Coverage"
    ),
    "micro_claim_coverage": (
        "Micro Claim Coverage"
    ),
    "complete_evidence_rate": (
        "Complete Evidence Rate"
    ),
    "any_evidence_rate": (
        "Any Evidence Rate"
    )
}

for metric in metric_names:
    print(
        f"{labels[metric]:<25} | "
        f"{dense_summary[metric]:>8.4f} | "
        f"{reranked_summary[metric]:>10.4f} | "
        f"{delta[metric]:>+8.4f}"
    )


print("\nPER-QUESTION CLAIM COVERAGE")

for item in per_question:
    dense = item["dense_top5"]
    reranked = item["reranked_top5"]

    print(
        f"{item['id']} | "
        f"Dense: "
        f"{dense['covered_claims']}/"
        f"{dense['total_claims']} | "
        f"Reranked: "
        f"{reranked['covered_claims']}/"
        f"{reranked['total_claims']} | "
        f"Complete: "
        f"{dense['complete_evidence']:.0f}"
        f" -> "
        f"{reranked['complete_evidence']:.0f}"
    )


print(f"\nSaved to: {output_path}")