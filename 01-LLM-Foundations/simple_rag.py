from openai import OpenAI
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

# 1. Load embedding model
embedding_model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# 2. Small knowledge base
documents = [
    "Cybersecurity protects networks.",
    "Machine learning learns patterns from data.",
    "Iraq has a hot climate.",
    "Large language models process natural language.",
    "Firewalls control network traffic."
]

# 3. User question
query = "كيف يمكنني حماية شبكة الحاسوب؟"

# 4. Create embeddings
document_embeddings = embedding_model.encode(documents)
query_embedding = embedding_model.encode(query)

# 5. Semantic similarity
similarities = cos_sim(query_embedding, document_embeddings)[0]

# 6. Retrieve Top-K
K = 2
top_results = similarities.argsort(descending=True)[:K]

# 7. Build context
context = "\n".join(
    documents[index] for index in top_results
)

print("Retrieved Context:")
print(context)

# 8. Connect to the LLM
client = OpenAI()

prompt = f"""
Answer the question using only the provided context.
If the context does not contain enough information, say so.

Context:
{context}

Question:
{query}
"""

# 9. Generate grounded answer
response = client.responses.create(
    model="gpt-5.6-luna",
    input=prompt
)

print("\nRAG Answer:")
print(response.output_text)