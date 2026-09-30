from pathlib import Path
import json

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


# 1. إعداد المسارات
project_folder = Path(__file__).parent

chunks_path = project_folder / "chunks.json"
questions_path = project_folder / "evaluation_questions.json"
results_path = project_folder / "retrieval_candidates.json"


# 2. إعدادات التقييم
embedding_model_name = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

top_k = 5


# 3. تحميل المقاطع وأسئلة التقييم
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

print(f"Loaded chunks: {len(chunks)}")
print(f"Loaded evaluation questions: {len(questions)}")


# 4. تحميل نموذج التمثيل الدلالي
embedding_model = SentenceTransformer(
    embedding_model_name
)


# 5. إنشاء Embeddings للمقاطع
print("\nCreating chunk embeddings...")

chunk_embeddings = embedding_model.encode(
    chunk_texts,
    convert_to_tensor=True,
    normalize_embeddings=True,
    show_progress_bar=True
)


# 6. إنشاء Embeddings لجميع الأسئلة
print("\nCreating query embeddings...")

query_embeddings = embedding_model.encode(
    retrieval_queries,
    convert_to_tensor=True,
    normalize_embeddings=True,
    show_progress_bar=False
)


# 7. حساب التشابه بين الأسئلة والمقاطع
similarity_matrix = cos_sim(
    query_embeddings,
    chunk_embeddings
)


# 8. استخراج أفضل خمسة مقاطع لكل سؤال
evaluation_results = []

for question_index, question in enumerate(questions):
    similarities = similarity_matrix[question_index]

    top_results = similarities.argsort(
        descending=True
    )[:top_k]

    candidates = []

    print("\n" + "=" * 80)
    print(f"Question ID: {question['id']}")
    print(f"Arabic question: {question['question_ar']}")
    print(
        "Retrieval query: "
        f"{question['retrieval_query_en']}"
    )

    for rank, index in enumerate(
        top_results,
        start=1
    ):
        chunk_index = index.item()
        chunk = chunks[chunk_index]
        score = similarities[chunk_index].item()

        candidate = {
            "rank": rank,
            "page": chunk["page"],
            "chunk_id": chunk["chunk_id"],
            "score": round(score, 4),
            "text": chunk["text"]
        }

        candidates.append(candidate)

        preview = " ".join(
            chunk["text"].split()
        )[:500]

        print("\n" + "-" * 80)
        print(
            f"Rank: {rank} | "
            f"Page: {chunk['page']} | "
            f"Chunk: {chunk['chunk_id']} | "
            f"Score: {score:.4f}"
        )
        print(preview)

    evaluation_results.append(
        {
            "id": question["id"],
            "question_ar": question["question_ar"],
            "retrieval_query_en": question[
                "retrieval_query_en"
            ],
            "candidates": candidates
        }
    )


# 9. حفظ النتائج للمراجعة اليدوية
results_path.write_text(
    json.dumps(
        evaluation_results,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print("\n" + "=" * 80)
print("Retrieval candidates saved to:")
print(results_path)
# 10. حساب مقاييس تقييم الاسترجاع
metrics_path = project_folder / "retrieval_metrics.json"

answerable_questions = [
    question
    for question in questions
    if question.get("answerable", True)
]

excluded_questions = [
    {
        "id": question["id"],
        "reason": question.get(
            "exclusion_reason",
            "Marked as unanswerable"
        )
    }
    for question in questions
    if not question.get("answerable", True)
]

results_by_id = {
    result["id"]: result
    for result in evaluation_results
}

per_question_metrics = []


# 11. مقارنة المقاطع المسترجعة مع Gold Chunks
for question in answerable_questions:
    question_id = question["id"]

    gold_chunk_ids = set(
        question["relevant_chunk_ids"]
    )

    if not gold_chunk_ids:
        raise ValueError(
            f"No Gold Chunks defined for {question_id}"
        )

    candidates = results_by_id[
        question_id
    ]["candidates"]

    retrieved_chunk_ids = [
        candidate["chunk_id"]
        for candidate in candidates
    ]

    relevant_ranks = [
        candidate["rank"]
        for candidate in candidates
        if candidate["chunk_id"] in gold_chunk_ids
    ]

    retrieved_gold_ids = [
        candidate["chunk_id"]
        for candidate in candidates
        if candidate["chunk_id"] in gold_chunk_ids
    ]

    retrieved_relevant_count = len(
        retrieved_gold_ids
    )

    recall_at_k = (
        retrieved_relevant_count
        / len(gold_chunk_ids)
    )

    precision_at_k = (
        retrieved_relevant_count
        / top_k
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

    per_question_metrics.append(
        {
            "id": question_id,
            "gold_chunk_ids": sorted(
                gold_chunk_ids
            ),
            "retrieved_chunk_ids": (
                retrieved_chunk_ids
            ),
            "retrieved_gold_ids": (
                retrieved_gold_ids
            ),
            f"recall_at_{top_k}": round(
                recall_at_k,
                4
            ),
            f"precision_at_{top_k}": round(
                precision_at_k,
                4
            ),
            f"hit_at_{top_k}": round(
                hit_at_k,
                4
            ),
            "reciprocal_rank": round(
                reciprocal_rank,
                4
            )
        }
    )


# 12. حساب المتوسط العام
evaluated_count = len(
    per_question_metrics
)

mean_recall = sum(
    item[f"recall_at_{top_k}"]
    for item in per_question_metrics
) / evaluated_count

mean_precision = sum(
    item[f"precision_at_{top_k}"]
    for item in per_question_metrics
) / evaluated_count

mean_hit_rate = sum(
    item[f"hit_at_{top_k}"]
    for item in per_question_metrics
) / evaluated_count

mean_reciprocal_rank = sum(
    item["reciprocal_rank"]
    for item in per_question_metrics
) / evaluated_count


# 13. إنشاء تقرير التقييم
metrics_report = {
    "configuration": {
        "embedding_model": embedding_model_name,
        "top_k": top_k,
        "total_questions": len(questions),
        "evaluated_questions": evaluated_count,
        "excluded_questions": len(
            excluded_questions
        )
    },
    "per_question": per_question_metrics,
    "summary": {
        f"mean_recall_at_{top_k}": round(
            mean_recall,
            4
        ),
        f"mean_precision_at_{top_k}": round(
            mean_precision,
            4
        ),
        f"hit_rate_at_{top_k}": round(
            mean_hit_rate,
            4
        ),
        f"mrr_at_{top_k}": round(
            mean_reciprocal_rank,
            4
        )
    },
    "excluded": excluded_questions
}


# 14. حفظ التقرير
metrics_path.write_text(
    json.dumps(
        metrics_report,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)


# 15. عرض النتائج
print("\n" + "=" * 80)
print("RETRIEVAL EVALUATION RESULTS")

for item in per_question_metrics:
    print(
        f"{item['id']} | "
        f"Recall@{top_k}: "
        f"{item[f'recall_at_{top_k}']:.2f} | "
        f"Precision@{top_k}: "
        f"{item[f'precision_at_{top_k}']:.2f} | "
        f"RR: {item['reciprocal_rank']:.2f} | "
        f"Hit@{top_k}: "
        f"{item[f'hit_at_{top_k}']:.2f}"
    )

print("\nOverall Results:")
print(
    f"Mean Recall@{top_k}: "
    f"{mean_recall:.2f}"
)
print(
    f"Mean Precision@{top_k}: "
    f"{mean_precision:.2f}"
)
print(
    f"Hit Rate@{top_k}: "
    f"{mean_hit_rate:.2f}"
)
print(
    f"MRR@{top_k}: "
    f"{mean_reciprocal_rank:.2f}"
)

print("\nExcluded questions:")
for item in excluded_questions:
    print(
        f"{item['id']}: {item['reason']}"
    )

print("\nMetrics saved to:")
print(metrics_path)