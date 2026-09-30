from pathlib import Path
import json

from sentence_transformers import (
    SentenceTransformer,
    CrossEncoder
)
from sentence_transformers.util import cos_sim


project_folder = Path(__file__).parent

chunks_path = project_folder / "chunks.json"
questions_path = (
    project_folder / "evaluation_questions.json"
)

candidates_path = (
    project_folder
    / "retrieval_candidates_dense20_reranked.json"
)

metrics_path = (
    project_folder
    / "retrieval_metrics_dense20_reranked5.json"
)

embedding_model_name = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

reranker_model_name = (
    "cross-encoder/"
    "ms-marco-MiniLM-L6-v2"
)

candidate_k = 20
final_k = 5


def evaluate_ranking(
    ranked_candidates,
    gold_chunk_ids,
    k
):
    selected = ranked_candidates[:k]

    retrieved_gold = [
        candidate
        for candidate in selected
        if candidate["chunk_id"] in gold_chunk_ids
    ]

    relevant_ranks = [
        rank
        for rank, candidate in enumerate(
            selected,
            start=1
        )
        if candidate["chunk_id"] in gold_chunk_ids
    ]

    retrieved_count = len(retrieved_gold)

    recall = (
        retrieved_count
        / len(gold_chunk_ids)
    )

    precision = (
        retrieved_count
        / k
    )

    hit = (
        1.0
        if relevant_ranks
        else 0.0
    )

    reciprocal_rank = (
        1.0 / min(relevant_ranks)
        if relevant_ranks
        else 0.0
    )

    return {
        "retrieved_chunk_ids": [
            candidate["chunk_id"]
            for candidate in selected
        ],
        "retrieved_gold_ids": [
            candidate["chunk_id"]
            for candidate in retrieved_gold
        ],
        "recall": round(recall, 4),
        "precision": round(precision, 4),
        "hit": round(hit, 4),
        "reciprocal_rank": round(
            reciprocal_rank,
            4
        )
    }


def summarize(per_question, method_name):
    count = len(per_question)

    return {
        "mean_recall": round(
            sum(
                item[method_name]["recall"]
                for item in per_question
            ) / count,
            4
        ),
        "mean_precision": round(
            sum(
                item[method_name]["precision"]
                for item in per_question
            ) / count,
            4
        ),
        "hit_rate": round(
            sum(
                item[method_name]["hit"]
                for item in per_question
            ) / count,
            4
        ),
        "mrr": round(
            sum(
                item[method_name][
                    "reciprocal_rank"
                ]
                for item in per_question
            ) / count,
            4
        )
    }


chunks = json.loads(
    chunks_path.read_text(encoding="utf-8")
)

questions = json.loads(
    questions_path.read_text(encoding="utf-8")
)

chunk_texts = [
    chunk["text"]
    for chunk in chunks
]

retrieval_queries = [
    question["retrieval_query_en"]
    for question in questions
]


print(f"Corpus chunks: {len(chunks)}")
print(f"Questions: {len(questions)}")
print(f"Candidate K: {candidate_k}")
print(f"Final K: {final_k}")


embedding_model = SentenceTransformer(
    embedding_model_name
)

print("\nCreating dense embeddings...")

chunk_embeddings = embedding_model.encode(
    chunk_texts,
    convert_to_tensor=True,
    normalize_embeddings=True,
    show_progress_bar=True
)

query_embeddings = embedding_model.encode(
    retrieval_queries,
    convert_to_tensor=True,
    normalize_embeddings=True,
    show_progress_bar=False
)

similarity_matrix = cos_sim(
    query_embeddings,
    chunk_embeddings
)


print("\nLoading Cross-Encoder reranker...")

reranker = CrossEncoder(
    reranker_model_name
)


all_candidate_results = []
per_question_metrics = []


for question_index, question in enumerate(
    questions
):
    question_id = question["id"]
    query = question["retrieval_query_en"]

    similarities = similarity_matrix[
        question_index
    ]

    dense_indices = similarities.argsort(
        descending=True
    )[:candidate_k]

    dense_candidates = []

    for dense_rank, tensor_index in enumerate(
        dense_indices,
        start=1
    ):
        chunk_index = tensor_index.item()
        chunk = chunks[chunk_index]

        dense_candidates.append(
            {
                "dense_rank": dense_rank,
                "chunk_id": chunk["chunk_id"],
                "page": chunk["page"],
                "dense_score": round(
                    similarities[
                        chunk_index
                    ].item(),
                    6
                ),
                "text": chunk["text"]
            }
        )

    query_passage_pairs = [
        [
            query,
            candidate["text"]
        ]
        for candidate in dense_candidates
    ]

    rerank_scores = reranker.predict(
        query_passage_pairs,
        batch_size=16,
        show_progress_bar=False
    )

    for candidate, score in zip(
        dense_candidates,
        rerank_scores
    ):
        candidate["rerank_score"] = float(
            score
        )

    reranked_candidates = sorted(
        dense_candidates,
        key=lambda item: item["rerank_score"],
        reverse=True
    )

    for rerank_rank, candidate in enumerate(
        reranked_candidates,
        start=1
    ):
        candidate["rerank_rank"] = rerank_rank
        candidate["rerank_score"] = round(
            candidate["rerank_score"],
            6
        )
        candidate["selected_for_final_top5"] = (
            rerank_rank <= final_k
        )

    all_candidate_results.append(
        {
            "id": question_id,
            "question_ar": question[
                "question_ar"
            ],
            "retrieval_query_en": query,
            "reranked_candidates": (
                reranked_candidates
            )
        }
    )

    if not question.get("answerable", True):
        continue

    gold_chunk_ids = set(
        question["relevant_chunk_ids"]
    )

    if not gold_chunk_ids:
        raise ValueError(
            f"No Gold Chunks for {question_id}"
        )

    dense_order = sorted(
        dense_candidates,
        key=lambda item: item["dense_rank"]
    )

    candidate_gold_count = sum(
        1
        for candidate in dense_order
        if candidate["chunk_id"] in gold_chunk_ids
    )

    candidate_recall = (
        candidate_gold_count
        / len(gold_chunk_ids)
    )

    gold_rank_transitions = [
        {
            "chunk_id": candidate["chunk_id"],
            "dense_rank": candidate[
                "dense_rank"
            ],
            "rerank_rank": candidate[
                "rerank_rank"
            ],
            "dense_score": candidate[
                "dense_score"
            ],
            "rerank_score": candidate[
                "rerank_score"
            ]
        }
        for candidate in reranked_candidates
        if candidate["chunk_id"] in gold_chunk_ids
    ]

    per_question_metrics.append(
        {
            "id": question_id,
            "gold_chunk_ids": sorted(
                gold_chunk_ids
            ),
            "candidate_recall_at_20": round(
                candidate_recall,
                4
            ),
            "gold_rank_transitions": (
                gold_rank_transitions
            ),
            "dense_top5": evaluate_ranking(
                dense_order,
                gold_chunk_ids,
                final_k
            ),
            "reranked_top5": evaluate_ranking(
                reranked_candidates,
                gold_chunk_ids,
                final_k
            )
        }
    )


dense_summary = summarize(
    per_question_metrics,
    "dense_top5"
)

reranked_summary = summarize(
    per_question_metrics,
    "reranked_top5"
)

delta = {
    metric: round(
        reranked_summary[metric]
        - dense_summary[metric],
        4
    )
    for metric in dense_summary
}

mean_candidate_recall = round(
    sum(
        item["candidate_recall_at_20"]
        for item in per_question_metrics
    )
    / len(per_question_metrics),
    4
)


metrics_report = {
    "configuration": {
        "embedding_model": (
            embedding_model_name
        ),
        "reranker_model": (
            reranker_model_name
        ),
        "candidate_k": candidate_k,
        "final_k": final_k,
        "total_questions": len(questions),
        "evaluated_questions": len(
            per_question_metrics
        )
    },
    "candidate_generation": {
        "mean_recall_at_20": (
            mean_candidate_recall
        )
    },
    "comparison": {
        "dense_top5": dense_summary,
        "reranked_top5": reranked_summary,
        "delta": delta
    },
    "per_question": per_question_metrics
}


candidates_path.write_text(
    json.dumps(
        all_candidate_results,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

metrics_path.write_text(
    json.dumps(
        metrics_report,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)


print("\nRETRIEVAL COMPARISON")

print(
    f"{'Metric':<16} | "
    f"{'Dense@5':>8} | "
    f"{'Reranked@5':>10} | "
    f"{'Delta':>8}"
)

print("-" * 54)

metric_labels = {
    "mean_recall": "Mean Recall",
    "mean_precision": "Mean Precision",
    "hit_rate": "Hit Rate",
    "mrr": "MRR"
}

for metric, label in metric_labels.items():
    print(
        f"{label:<16} | "
        f"{dense_summary[metric]:>8.4f} | "
        f"{reranked_summary[metric]:>10.4f} | "
        f"{delta[metric]:>+8.4f}"
    )


print("\nGOLD RANK TRANSITIONS")

for item in per_question_metrics:
    transitions = ", ".join(
        (
            f"Chunk {transition['chunk_id']}: "
            f"{transition['dense_rank']}"
            f" -> "
            f"{transition['rerank_rank']}"
        )
        for transition in item[
            "gold_rank_transitions"
        ]
    )

    print(
        f"{item['id']} | "
        f"{transitions} | "
        f"Dense Recall@5: "
        f"{item['dense_top5']['recall']:.2f} | "
        f"Reranked Recall@5: "
        f"{item['reranked_top5']['recall']:.2f}"
    )


print(
    "\nCandidate Mean Recall@20: "
    f"{mean_candidate_recall:.4f}"
)

print(f"\nCandidates saved to: {candidates_path}")
print(f"Metrics saved to: {metrics_path}")