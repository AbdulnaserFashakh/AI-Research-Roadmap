from pathlib import Path
import json

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


project_folder = Path(__file__).parent

chunks_path = project_folder / "chunks.json"
questions_path = project_folder / "evaluation_questions.json"

output_path = (
    project_folder
    / "top_k_sensitivity_dense_baseline.json"
)

model_name = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

k_values = [1, 3, 5, 10, 20]


chunks = json.loads(
    chunks_path.read_text(encoding="utf-8")
)

questions = json.loads(
    questions_path.read_text(encoding="utf-8")
)

answerable_questions = [
    question
    for question in questions
    if question.get("answerable", True)
]

for question in answerable_questions:
    if not question.get("relevant_chunk_ids"):
        raise ValueError(
            "Missing Gold Chunks for "
            f"{question['id']}"
        )


chunk_texts = [
    chunk["text"]
    for chunk in chunks
]

retrieval_queries = [
    question["retrieval_query_en"]
    for question in answerable_questions
]


print(f"Corpus chunks: {len(chunks)}")
print(
    "Answerable questions: "
    f"{len(answerable_questions)}"
)
print(f"K values: {k_values}")


model = SentenceTransformer(model_name)

print("\nCreating chunk embeddings...")

chunk_embeddings = model.encode(
    chunk_texts,
    convert_to_tensor=True,
    normalize_embeddings=True,
    show_progress_bar=True
)

print("\nCreating query embeddings...")

query_embeddings = model.encode(
    retrieval_queries,
    convert_to_tensor=True,
    normalize_embeddings=True,
    show_progress_bar=False
)

similarity_matrix = cos_sim(
    query_embeddings,
    chunk_embeddings
)


rankings_by_question = {}

for question_index, question in enumerate(
    answerable_questions
):
    scores = similarity_matrix[question_index]

    ranked_indices = scores.argsort(
        descending=True
    ).tolist()

    ranked_results = []

    for rank, chunk_index in enumerate(
        ranked_indices,
        start=1
    ):
        chunk = chunks[chunk_index]

        ranked_results.append(
            {
                "rank": rank,
                "chunk_id": chunk["chunk_id"],
                "page": chunk["page"],
                "score": round(
                    scores[chunk_index].item(),
                    4
                )
            }
        )

    rankings_by_question[
        question["id"]
    ] = ranked_results


gold_rank_analysis = []

for question in answerable_questions:
    question_id = question["id"]

    gold_chunk_ids = set(
        question["relevant_chunk_ids"]
    )

    ranked_results = rankings_by_question[
        question_id
    ]

    gold_ranks = [
        {
            "chunk_id": result["chunk_id"],
            "rank": result["rank"],
            "page": result["page"],
            "score": result["score"]
        }
        for result in ranked_results
        if result["chunk_id"] in gold_chunk_ids
    ]

    gold_rank_analysis.append(
        {
            "id": question_id,
            "gold_chunk_ids": sorted(
                gold_chunk_ids
            ),
            "gold_ranks": gold_ranks,
            "first_gold_rank": min(
                item["rank"]
                for item in gold_ranks
            ),
            "all_gold_rank": max(
                item["rank"]
                for item in gold_ranks
            ),
            "top_20_chunk_ids": [
                item["chunk_id"]
                for item in ranked_results[:20]
            ]
        }
    )


sensitivity_results = []

for k in k_values:
    per_question = []

    for question in answerable_questions:
        question_id = question["id"]

        gold_chunk_ids = set(
            question["relevant_chunk_ids"]
        )

        retrieved = rankings_by_question[
            question_id
        ][:k]

        retrieved_gold = [
            result
            for result in retrieved
            if result["chunk_id"] in gold_chunk_ids
        ]

        relevant_ranks = [
            result["rank"]
            for result in retrieved_gold
        ]

        retrieved_relevant_count = len(
            retrieved_gold
        )

        recall_at_k = (
            retrieved_relevant_count
            / len(gold_chunk_ids)
        )

        precision_at_k = (
            retrieved_relevant_count
            / k
        )

        hit_at_k = (
            1.0
            if relevant_ranks
            else 0.0
        )

        reciprocal_rank = (
            1.0 / min(relevant_ranks)
            if relevant_ranks
            else 0.0
        )

        per_question.append(
            {
                "id": question_id,
                "gold_chunk_ids": sorted(
                    gold_chunk_ids
                ),
                "retrieved_gold_ids": [
                    result["chunk_id"]
                    for result in retrieved_gold
                ],
                "recall": round(
                    recall_at_k,
                    4
                ),
                "precision": round(
                    precision_at_k,
                    4
                ),
                "hit": round(
                    hit_at_k,
                    4
                ),
                "reciprocal_rank": round(
                    reciprocal_rank,
                    4
                )
            }
        )

    question_count = len(per_question)

    summary = {
        "mean_recall": round(
            sum(
                item["recall"]
                for item in per_question
            ) / question_count,
            4
        ),
        "mean_precision": round(
            sum(
                item["precision"]
                for item in per_question
            ) / question_count,
            4
        ),
        "hit_rate": round(
            sum(
                item["hit"]
                for item in per_question
            ) / question_count,
            4
        ),
        "mrr": round(
            sum(
                item["reciprocal_rank"]
                for item in per_question
            ) / question_count,
            4
        )
    }

    sensitivity_results.append(
        {
            "k": k,
            "summary": summary,
            "per_question": per_question
        }
    )


report = {
    "configuration": {
        "embedding_model": model_name,
        "corpus_size": len(chunks),
        "answerable_questions": len(
            answerable_questions
        ),
        "k_values": k_values
    },
    "gold_rank_analysis": gold_rank_analysis,
    "sensitivity_results": sensitivity_results
}

output_path.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)


print("\nTOP-K SENSITIVITY RESULTS")

print(
    f"{'K':>3} | "
    f"{'Recall':>8} | "
    f"{'Precision':>9} | "
    f"{'Hit Rate':>8} | "
    f"{'MRR':>6}"
)

print("-" * 50)

for result in sensitivity_results:
    summary = result["summary"]

    print(
        f"{result['k']:>3} | "
        f"{summary['mean_recall']:>8.4f} | "
        f"{summary['mean_precision']:>9.4f} | "
        f"{summary['hit_rate']:>8.4f} | "
        f"{summary['mrr']:>6.4f}"
    )


print("\nGOLD RANK ANALYSIS")

for item in gold_rank_analysis:
    rank_text = ", ".join(
        (
            f"Chunk {result['chunk_id']}="
            f"Rank {result['rank']}"
        )
        for result in item["gold_ranks"]
    )

    print(
        f"{item['id']} | "
        f"{rank_text} | "
        f"First Gold: {item['first_gold_rank']} | "
        f"All Gold: {item['all_gold_rank']}"
    )


print(f"\nSaved to: {output_path}")