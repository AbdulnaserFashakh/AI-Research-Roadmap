from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

sentences = [
    "Cybersecurity protects computer systems.",
    "الأمن السيبراني يحمي أنظمة الحاسوب.",
    "I like Italian food."
]

embeddings = model.encode(sentences)

print("Number of sentences:", len(sentences))
print("Embedding dimensions:", embeddings.shape[1])

print("\nFirst 10 values of each embedding:")

for sentence, vector in zip(sentences, embeddings):
    print("\n", sentence)
    print(vector[:10])

print("\nSemantic Similarity")

similarity_1 = cos_sim(embeddings[0], embeddings[1]).item()
similarity_2 = cos_sim(embeddings[0], embeddings[2]).item()

print(
    "English cybersecurity vs Arabic cybersecurity:",
    round(similarity_1, 4)
)

print(
    "Cybersecurity vs Italian food:",
    round(similarity_2, 4)
)