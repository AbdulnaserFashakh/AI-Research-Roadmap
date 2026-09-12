from pathlib import Path
import json
import re

from pypdf import PdfReader

# 1. Define paths
project_folder = Path(__file__).parent
pdf_path = project_folder / "data" / "cyberbullying_paper.pdf"
output_path = project_folder / "chunks.json"

# 2. Chunk settings
CHUNK_SIZE = 80
CHUNK_OVERLAP = 20


def clean_text(text):
    """Clean text extracted from the PDF."""

    # Join words separated by line-break hyphenation
    text = re.sub(r"-\s*\n\s*", "", text)

    # Replace repeated spaces and line breaks with one space
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def split_into_chunks(text, page_number):
    """Split one page into overlapping word chunks."""

    words = text.split()
    chunks = []

    start = 0

    while start < len(words):
        end = start + CHUNK_SIZE
        chunk_words = words[start:end]

        if not chunk_words:
            break

        chunks.append(
            {
                "page": page_number,
                "word_count": len(chunk_words),
                "text": " ".join(chunk_words)
            }
        )

        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


# 3. Read the PDF
reader = PdfReader(pdf_path)
all_chunks = []

# 4. Extract, clean and split every page
for page_number, page in enumerate(reader.pages, start=1):
    raw_text = page.extract_text() or ""
    cleaned_text = clean_text(raw_text)

    page_chunks = split_into_chunks(
        cleaned_text,
        page_number
    )

    for chunk in page_chunks:
        chunk["chunk_id"] = len(all_chunks) + 1
        all_chunks.append(chunk)

    print(
        f"Page {page_number}: "
        f"{len(page_chunks)} chunks created"
    )

# 5. Save chunks as JSON
output_path.write_text(
    json.dumps(
        all_chunks,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

# 6. Display results
print(f"\nTotal chunks: {len(all_chunks)}")
print(f"Chunks saved to: {output_path}")

print("\nFirst three chunks:")

for chunk in all_chunks[:3]:
    print(
        f"\nChunk {chunk['chunk_id']} "
        f"| Page {chunk['page']} "
        f"| Words: {chunk['word_count']}"
    )
    print(chunk["text"])