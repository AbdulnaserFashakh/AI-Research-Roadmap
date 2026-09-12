from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

# Load the multilingual embedding model
model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# Our small knowledge base
documents = [
    "Cybersecurity protects networks.",
    "Machine learning learns patterns from data.",
    "Iraq has a hot climate.",
    "Large language models process natural language.",
    "Firewalls control network traffic."
]

# User question
query = "كيف يمكنني حماية شبكة الحاسوب؟"

# Convert documents and question into embeddings
document_embeddings = model.encode(documents)
query_embedding = model.encode(query)

# Compare the question with every document
similarities = cos_sim(query_embedding, document_embeddings)[0]

print("Question:")
print(query)

print("\nResults:")

for document, score in zip(documents, similarities):
    print(f"{score.item():.4f}  ->  {document}")

# Find the document with the highest similarity
# Retrieve Top-K most similar documents
K = 3

top_results = similarities.argsort(descending=True)[:K]

print(f"\nTop-{K} Results:")

for rank, index in enumerate(top_results, start=1):
    print(
        f"{rank}. {documents[index]} "
        f"(Similarity: {similarities[index].item():.4f})"
    )
    # Build context from Top-K results
context = "\n".join(
    documents[index] for index in top_results
)

print("\nContext for the LLM:")
print(context)