from pathlib import Path
import json

from ollama import chat


project_folder = Path(__file__).parent

# Load the evaluation questions.
questions = json.loads(
    (project_folder / "evaluation_questions.json")
    .read_text(encoding="utf-8")
)

question = next(
    item for item in questions
    if item["id"] == "Q01"
)

# Load the saved Dense retrieval results.
retrieval_results = json.loads(
    (project_folder / "retrieval_candidates_k5_baseline.json")
    .read_text(encoding="utf-8")
)

question_results = next(
    item for item in retrieval_results
    if item["id"] == question["id"]
)

selected_chunks = question_results["candidates"][:5]

if len(selected_chunks) != 5:
    raise ValueError("Expected five retrieved chunks for Q01.")

# Build context from the saved chunks.
context = "\n\n".join(
    f"[Page {chunk['page']}, Chunk {chunk['chunk_id']}]\n"
    f"{chunk['text']}"
    for chunk in selected_chunks
)

prompt = f"""
أنت مساعد بحثي.

اعتمد فقط على السياق المرفق.
لا تستخدم معرفتك السابقة.
اذكر الدقة لكل نموذج إذا كانت موجودة في السياق.
لا تستنتج أرقاماً غير مذكورة.
إذا تساوى نموذجان في الدقة، اذكر التعادل.
بعد كل ادعاء اذكر مصدره بهذه الصيغة:
[Page X, Chunk Y]

إذا لم تجد الأدلة اللازمة للإجابة، قل:
السياق غير كافٍ للإجابة.
يمكنك ذكر المعلومات المتاحة مع تحديد ما ينقصها.

السياق:
{context}

السؤال:
{question["question_ar"]}

أجب باللغة العربية.
"""

model_name = "qwen3:4b"

print("Question:", question["question_ar"])
print(
    "Retrieved chunk IDs:",
    [chunk["chunk_id"] for chunk in selected_chunks]
)
print("\nGenerating answer...")

response = chat(
    model=model_name,
    messages=[
        {"role": "user", "content": prompt}
    ],
    options={
        "temperature": 0,
        "seed": 42
    }
)

answer = response.message.content

# Save the answer and the evidence used to generate it.
result = {
    "question_id": question["id"],
    "question_ar": question["question_ar"],
    "retrieval_method": "Dense@5",
    "model": model_name,
    "temperature": 0,
    "seed": 42,
    "retrieved_chunks": selected_chunks,
    "prompt": prompt,
    "answer": answer
}

output_path = project_folder / "end_to_end_q01_dense5.json"

output_path.write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("\nRAG Answer:")
print(answer)
print("\nSaved:", output_path.name)