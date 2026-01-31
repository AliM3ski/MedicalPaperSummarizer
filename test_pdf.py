from ingestion.pdf_loader import PDFLoader

# Try with PyMuPDF
loader = PDFLoader(use_pymupdf=True)

try:
    text = loader.load("Hip_Study.pdf")
    print("[OK] PDF loaded successfully!")
    print(f"Extracted {len(text)} characters")
    print("\nFirst 500 characters:")
    print(text[:500])
except Exception as e:
    print(f"[ERROR] {e}")