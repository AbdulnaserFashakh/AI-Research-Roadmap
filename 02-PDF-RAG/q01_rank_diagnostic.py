from pathlib import Path
import json

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


project_folder = Path(__file__).parent

chunks_path = project_folder / "chunks.json"
questions_path = project_folder / "evaluation_questions.json"
output_path = project_folder / "q01_rank_diagnostic.json"

model_name = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

question_id = "Q01"
top_n = 20


chunks = json.loads(
    chunks_path.read_text(encoding="utf-8")
)

questions = json.loads(
    questions_path.read_text(encoding="utf-8")
)

question = next(
    item
    for item in questions
    if item["id"] == question_id
)

gold_chunk_ids = set(
    question["relevant_chunk_ids"]
)

chunk_texts = [
    chunk["text"]
    for chunk in chunks
]


print(f"Question: {question_id}")
print(f"Query: {question['retrieval_query_en']}")
print(f"Gold chunks: {sorted(gold_chunk_ids)}")
print(f"Corpus size: {len(chunks)}")


model = SentenceTransformer(model_name)

print("\nCreating embeddings...")

chunk_embeddings = model.encode(
    chunk_texts,
    convert_to_tensor=True,
    normalize_embeddings=True,
    show_progress_bar=True
)

query_embedding = model.encode(
    question["retrieval_query_en"],
    convert_to_tensor=True,
    normalize_embeddings=True
)

scores = cos_sim(
    query_embedding,
    chunk_embeddings
)[0]

ranking = scores.argsort(
    descending=True
)


top_results = []
gold_results = []

for rank, tensor_index in enumerate(
    ranking,
    start=1
):
    chunk_index = tensor_index.item()
    chunk = chunks[chunk_index]

    result = {
        "rank": rank,
        "page": chunk["page"],
        "chunk_id": chunk["chunk_id"],
        "score": round(
            scores[chunk_index].item(),
            4
        ),
        "text": chunk["text"]
    }

    if rank <= top_n:
        top_results.append(result)

    if chunk["chunk_id"] in gold_chunk_ids:
        gold_results.append(result)


print("\nTOP 20 RESULTS")

for result in top_results:
    marker = (
        " <-- GOLD"
        if result["chunk_id"] in gold_chunk_ids
        else ""
    )

    print(
        f"Rank: {result['rank']:>3} | "
        f"Page: {result['page']:>2} | "
        f"Chunk: {result['chunk_id']:>3} | "
        f"Score: {result['score']:.4f}"
        f"{marker}"
    )


print("\nGOLD CHUNK RANKS")

for result in gold_results:
    print(
        f"Chunk {result['chunk_id']} | "
        f"Rank: {result['rank']} | "
        f"Page: {result['page']} | "
        f"Score: {result['score']:.4f}"
    )


minimum_k_for_any_gold = min(
    result["rank"]
    for result in gold_results
)

minimum_k_for_all_gold = max(
    result["rank"]
    for result in gold_results
)

report = {
    "question_id": question_id,
    "query": question["retrieval_query_en"],
    "model": model_name,
    "corpus_size": len(chunks),
    "gold_chunk_ids": sorted(gold_chunk_ids),
    "minimum_k_for_any_gold": minimum_k_for_any_gold,
    "minimum_k_for_all_gold": minimum_k_for_all_gold,
    "gold_results": gold_results,
    f"top_{top_n}_results": top_results
}

output_path.write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print(
    "\nMinimum K for any Gold Chunk: "
    f"{minimum_k_for_any_gold}"
)

print(
    "Minimum K for all Gold Chunks: "
    f"{minimum_k_for_all_gold}"
)

print(f"\nSaved to: {output_path}")