from pathlib import Path
import json

from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
from ollama import chat

# 1. Define paths
project_folder = Path(__file__).parent
chunks_path = project_folder / "chunks.json"

# 2. Load PDF chunks
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

# 4. Create chunk embeddings
print("Creating chunk embeddings...")

chunk_embeddings = embedding_model.encode(
    chunk_texts,
    convert_to_tensor=True,
    normalize_embeddings=True,
    show_progress_bar=True
)

# 5. Define the user question
user_question = (
    "قارن دقة نماذج CNN وRNN وLSTM في نتائج تحليل المشاعر. "
    "ما النموذج الأفضل؟"
)

# English retrieval query to match the English paper
retrieval_query = (
    "Compare the accuracy of CNN, RNN, and LSTM models "
    "in the sentiment analysis results."
)

# 6. Create query embedding
query_embedding = embedding_model.encode(
    retrieval_query,
    convert_to_tensor=True,
    normalize_embeddings=True
)

# 7. Calculate similarity
similarities = cos_sim(
    query_embedding,
    chunk_embeddings
)[0]

# 8. Retrieve relevant chunks
K = 3
similarity_threshold = 0.50

top_results = similarities.argsort(
    descending=True
)[:K]

retrieved_chunks = []

for index in top_results:
    chunk_index = index.item()
    score = similarities[chunk_index].item()
    chunk = chunks[chunk_index]

    if score >= similarity_threshold:
        retrieved_chunks.append(
            {
                "chunk_id": chunk["chunk_id"],
                "page": chunk["page"],
                "score": score,
                "text": chunk["text"]
            }
        )

# 9. Display retrieved sources
print("\nRetrieved Sources:")

for source_number, chunk in enumerate(
    retrieved_chunks,
    start=1
):
    print("\n" + "=" * 70)
    print(f"Source: {source_number}")
    print(f"Page: {chunk['page']}")
    print(f"Chunk ID: {chunk['chunk_id']}")
    print(f"Similarity Score: {chunk['score']:.4f}")
    print("-" * 70)
    print(chunk["text"])

# 10. Stop if no sources passed the threshold
if not retrieved_chunks:
    print("\nRAG Answer:")
    print("لم يتم العثور على مصادر كافية للإجابة.")
    raise SystemExit

# 11. Build context with page citations
context_parts = []

for source_number, chunk in enumerate(
    retrieved_chunks,
    start=1
):
    context_parts.append(
        f"""
[Source {source_number}]
Page: {chunk['page']}
Chunk ID: {chunk['chunk_id']}
Text: {chunk['text']}
"""
    )

context = "\n".join(context_parts)

# 12. Build grounded RAG prompt
prompt = f"""
أنت مساعد بحثي.

اعتمد فقط على المعلومات الموجودة في السياق.
لا تستخدم معلومات من خارج السياق.
قارن النتائج الرقمية بوضوح.
بعد كل معلومة، اذكر الصفحة ورقم المقطع بهذه الصيغة:
[Page X, Chunk Y]

إذا لم يكن السياق كافياً، قل:
السياق غير كافٍ للإجابة.

السياق:
{context}

السؤال:
{user_question}

أجب باللغة العربية باختصار.
"""

# 13. Generate Arabic answer with local Qwen
response = chat(
    model="qwen3:4b",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

# 14. Display final answer
print("\n" + "=" * 70)
print("RAG Answer:")
print(response.message.content)