from pathlib import Path
from pypdf import PdfReader

# 1. Define file paths
project_folder = Path(__file__).parent
pdf_path = project_folder / "data" / "cyberbullying_paper.pdf"
output_path = project_folder / "extracted_text.txt"

# 2. Check that the PDF exists
if not pdf_path.exists():
    raise FileNotFoundError(f"PDF file not found: {pdf_path}")

# 3. Open the PDF
reader = PdfReader(pdf_path)

print(f"Number of pages: {len(reader.pages)}")

# 4. Extract text from every page
pages_text = []

for page_number, page in enumerate(reader.pages, start=1):
    page_text = page.extract_text() or ""

    pages_text.append(
        f"\n--- Page {page_number} ---\n{page_text}"
    )

    print(
        f"Page {page_number}: "
        f"{len(page_text)} characters extracted"
    )

# 5. Combine all pages
full_text = "\n".join(pages_text)

# 6. Save the extracted text
output_path.write_text(full_text, encoding="utf-8")

print(f"\nTotal extracted characters: {len(full_text)}")
print(f"Text saved to: {output_path}")

# 7. Display a short preview
print("\nText Preview:")
print(full_text[:1000])