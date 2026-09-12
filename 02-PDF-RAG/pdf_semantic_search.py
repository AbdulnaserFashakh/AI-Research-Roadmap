from pathlib import Path
import json

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

# 1. Define paths
project_folder = Path(__file__).parent
chunks_path = project_folder / "chunks.json"

# 2. Load chunks
chunks = json.loads(
    chunks_path.read_text(encoding="utf-8")
)

chunk_texts = [
    chunk["text"]
    for chunk in chunks
]

print(f"Loaded chunks: {len(chunks)}")

# 3. Load multilingual embedding model
embedding_model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# 4. Convert all chunks into embeddings
print("Creating chunk embeddings...")

chunk_embeddings = embedding_model.encode(
    chunk_texts,
    convert_to_tensor=True,
    normalize_embeddings=True,
    show_progress_bar=True
)

print(
    f"Embedding matrix shape: "
    f"{tuple(chunk_embeddings.shape)}"
)

# 5. Ask an Arabic research question
query = "Compare the accuracy of CNN, RNN, and LSTM models in the sentiment analysis results."

query_embedding = embedding_model.encode(
    query,
    convert_to_tensor=True,
    normalize_embeddings=True
)

# 6. Calculate semantic similarity
similarities = cos_sim(
    query_embedding,
    chunk_embeddings
)[0]

# 7. Retrieve Top-K chunks
K = 5
top_results = similarities.argsort(
    descending=True
)[:K]

# 8. Display results
print(f"\nQuestion: {query}")
print(f"\nTop-{K} Retrieved Chunks:")

for rank, index in enumerate(top_results, start=1):
    chunk_index = index.item()
    chunk = chunks[chunk_index]
    score = similarities[chunk_index].item()

    print("\n" + "=" * 70)
    print(f"Rank: {rank}")
    print(f"Chunk ID: {chunk['chunk_id']}")
    print(f"Page: {chunk['page']}")
    print(f"Similarity Score: {score:.4f}")
    print("-" * 70)
    print(chunk["text"])