from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from ollama import chat

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

# 5. Calculate semantic similarity
similarities = cos_sim(query_embedding, document_embeddings)[0]

# 6. Retrieve Top-K results
K = 3
similarity_threshold = 0.40

top_results = similarities.argsort(descending=True)[:K]

# 7. Filter weak results and store accepted sources
accepted_results = []

for index in top_results:
    document_index = index.item()
    score = similarities[document_index].item()

    if score >= similarity_threshold:
        accepted_results.append(
            {
                "source_id": len(accepted_results) + 1,
                "text": documents[document_index],
                "score": score
            }
        )

# 8. Display retrieved sources and similarity scores
print("\nRetrieved Sources:")

if accepted_results:
    for result in accepted_results:
        print(
            f"[Source {result['source_id']}] "
            f"Score: {result['score']:.4f}"
        )
        print(result["text"])
        print()
else:
    print("No relevant sources passed the similarity threshold.")

# 9. Build context
context = "\n".join(
    f"[Source {result['source_id']}] {result['text']}"
    for result in accepted_results
)

# 10. Stop if no relevant context exists
if not context:
    print("\nRAG Answer:")
    print("السياق غير كافٍ للإجابة.")
    raise SystemExit

# 11. Build RAG prompt
prompt = f"""
اعتمد فقط على المعلومات الموجودة في السياق التالي.
لا تستخدم معلومات من خارج السياق.
اذكر رقم المصدر المستخدم بين أقواس مربعة مثل [Source 1].
إذا كانت المعلومات غير كافية، قل: السياق غير كافٍ للإجابة.

Context:
{context}

Question:
{query}

أجب باللغة العربية باختصار.
"""

# 12. Generate answer using local Ollama model
response = chat(
    model="qwen3:4b",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

print("\nRAG Answer:")
print(response.message.content)