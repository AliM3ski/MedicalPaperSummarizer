# API Documentation

Complete reference for the Medical Paper Summarizer API.

## Table of Contents

1. [Main Summarizer](#main-summarizer)
2. [Document Loaders](#document-loaders)
3. [Text Processing](#text-processing)
4. [LLM Client](#llm-client)
5. [Output Schema](#output-schema)
6. [Configuration](#configuration)

---

## Main Summarizer

### MedicalPaperSummarizer

Main orchestrator class for paper summarization.

#### Constructor

```python
MedicalPaperSummarizer(
    primary_model: Optional[str] = None,
    fallback_model: Optional[str] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None
)
```

**Parameters:**
- `primary_model`: LLM model identifier (default: from config)
- `fallback_model`: Backup model if primary fails
- `chunk_size`: Token count per chunk (default: 1000)
- `chunk_overlap`: Overlapping tokens between chunks (default: 200)

**Example:**
```python
summarizer = MedicalPaperSummarizer(
    primary_model="claude-sonnet-4-20250514",
    chunk_size=1200
)
```

#### Methods

##### `summarize(file_path, title=None) -> PaperSummary`

Summarize a research paper.

**Parameters:**
- `file_path` (str): Path to PDF or XML file
- `title` (Optional[str]): Paper title (auto-extracted if None)

**Returns:**
- `PaperSummary`: Structured summary object

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If file format unsupported or processing fails
- `RuntimeError`: If LLM calls fail

**Example:**
```python
summary = summarizer.summarize("paper.pdf")
print(summary.title)
print(summary.key_findings)
```

##### `get_processing_stats() -> dict`

Get statistics about last processing run.

**Returns:**
- Dictionary with processing statistics

---

## Document Loaders

### PDFLoader

Extract text from PDF files.

#### Constructor

```python
PDFLoader(use_pymupdf: bool = False)
```

**Parameters:**
- `use_pymupdf`: Use PyMuPDF instead of pdfplumber (faster but less accurate)

#### Methods

##### `load(pdf_path: str) -> str`

Extract text from PDF.

**Parameters:**
- `pdf_path`: Path to PDF file

**Returns:**
- Extracted text as string

**Example:**
```python
loader = PDFLoader()
text = loader.load("paper.pdf")
```

##### `get_metadata(pdf_path: str) -> dict`

Extract PDF metadata.

**Returns:**
- Dictionary with title, author, page count, etc.

### XMLLoader

Extract text from PubMed Central XML files.

#### Methods

##### `load(xml_path: str) -> str`

Extract structured text from PMC XML.

**Parameters:**
- `xml_path`: Path to XML file

**Returns:**
- Extracted text with section markers

##### `get_metadata(xml_path: str) -> dict`

Extract article metadata including authors, DOI, keywords.

### TextCleaner

Clean and normalize extracted text.

#### Methods

##### `clean(text, remove_references=True, remove_figures_tables=True, remove_citations=False) -> str`

Clean extracted text.

**Parameters:**
- `text`: Raw text
- `remove_references`: Remove references section
- `remove_figures_tables`: Remove figure/table captions
- `remove_citations`: Remove inline citations

**Returns:**
- Cleaned text

**Example:**
```python
cleaner = TextCleaner()
cleaned = cleaner.clean(raw_text, remove_citations=True)
```

---

## Text Processing

### SectionParser

Parse papers into sections.

#### Methods

##### `parse(text: str) -> Dict[str, Section]`

Parse text into sections.

**Returns:**
- Dictionary mapping section names to Section objects

**Example:**
```python
parser = SectionParser()
sections = parser.parse(text)

for name, section in sections.items():
    print(f"{name}: {len(section.content)} chars")
```

##### `validate_sections(sections: Dict[str, Section]) -> bool`

Validate that essential sections are present.

##### `get_section_order(sections: Dict[str, Section]) -> List[str]`

Get sections in logical order.

### TextChunker

Chunk text for LLM processing.

#### Constructor

```python
TextChunker(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    encoding_name: str = "cl100k_base"
)
```

#### Methods

##### `chunk(text: str, section_name: Optional[str] = None) -> List[Chunk]`

Chunk text with overlap.

**Returns:**
- List of Chunk objects

**Example:**
```python
chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
chunks = chunker.chunk(text)

for i, chunk in enumerate(chunks):
    print(f"Chunk {i}: {chunk.token_count} tokens")
```

##### `count_tokens(text: str) -> int`

Count tokens in text.

##### `truncate_to_tokens(text: str, max_tokens: int) -> str`

Truncate text to maximum token count.

---

## LLM Client

### LLMClient

Unified client for LLM APIs with retry logic.

#### Constructor

```python
LLMClient(
    primary_model: Optional[str] = None,
    fallback_model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 4096
)
```

#### Methods

##### `complete(prompt, system_prompt=None, temperature=None, max_tokens=None, json_mode=False) -> str`

Get completion from LLM.

**Parameters:**
- `prompt`: User prompt
- `system_prompt`: System prompt
- `temperature`: Sampling temperature (0.0-1.0)
- `max_tokens`: Maximum response tokens
- `json_mode`: Request JSON-formatted response

**Returns:**
- Model response text

**Example:**
```python
client = LLMClient()
response = client.complete(
    prompt="Summarize this text...",
    system_prompt="You are a medical expert.",
    temperature=0.1
)
```

##### `parse_json_response(response: str) -> dict`

Parse JSON response, handling markdown code blocks.

---

## Output Schema

### PaperSummary

Structured summary of a research paper.

#### Fields

```python
class PaperSummary(BaseModel):
    title: str
    objective: str
    study_type: str
    population: str
    methods: str
    key_findings: List[str]
    limitations: List[str]
    author_conclusions: str
    keywords: List[str]
    summary_timestamp: datetime
    model_used: str
    safety_disclaimer: str
```

#### Methods

##### `to_markdown() -> str`

Convert summary to formatted markdown.

**Example:**
```python
summary = PaperSummary(...)
markdown = summary.to_markdown()
print(markdown)
```

##### `model_dump_json(indent=2) -> str`

Export to JSON string.

**Example:**
```python
json_str = summary.model_dump_json(indent=2)
with open("summary.json", "w") as f:
    f.write(json_str)
```

---

## Configuration

### Settings

Application configuration using Pydantic Settings.

#### Fields

```python
class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str
    openai_api_key: str
    
    # Model Configuration
    primary_model: str = "claude-sonnet-4-20250514"
    fallback_model: str = "gpt-4-turbo-preview"
    temperature: float = 0.2
    max_tokens: int = 4096
    
    # Chunking
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_section_chunks: int = 20
    
    # Processing
    max_retries: int = 3
    timeout: int = 60
    rate_limit_delay: float = 1.0
```

#### Usage

```python
from config import settings

print(f"Model: {settings.primary_model}")
print(f"Chunk size: {settings.chunk_size}")
```

Settings are loaded from:
1. `.env` file
2. Environment variables
3. Default values

---

## Error Handling

All main functions may raise:

- `FileNotFoundError`: File not found
- `ValueError`: Invalid input or processing error
- `RuntimeError`: LLM API failure
- `ValidationError`: Output validation failure

**Example:**
```python
try:
    summary = summarizer.summarize("paper.pdf")
except FileNotFoundError:
    print("File not found")
except ValueError as e:
    print(f"Processing error: {e}")
except RuntimeError as e:
    print(f"LLM error: {e}")
```

---

## Advanced Usage

### Custom Prompts

Modify prompt templates in `summarization/prompts.py`:

```python
from summarization.prompts import PromptTemplates

# Customize system prompt
PromptTemplates.SYSTEM_PROMPT = """
Your custom system prompt here...
"""
```

### Custom Section Detection

Add custom section patterns:

```python
from processing.section_parser import SectionParser

parser = SectionParser()
parser.HEADER_PATTERNS['custom_section'] = [
    r'\bMY CUSTOM SECTION\b'
]
```

### Batch Processing

```python
from pathlib import Path
from summarization.summarizer import MedicalPaperSummarizer

summarizer = MedicalPaperSummarizer()

for pdf_file in Path("papers/").glob("*.pdf"):
    summary = summarizer.summarize(str(pdf_file))
    output = Path(f"summaries/{pdf_file.stem}.json")
    output.write_text(summary.model_dump_json(indent=2))
```

---

## Type Hints

All functions include type hints for better IDE support:

```python
from typing import Optional, List, Dict
from output.schema import PaperSummary

def process_paper(
    file_path: str,
    custom_title: Optional[str] = None
) -> PaperSummary:
    ...
```

---

## Logging

Configure logging level:

```python
import logging

# Set to DEBUG for verbose output
logging.basicConfig(level=logging.DEBUG)

# Set to WARNING for minimal output
logging.basicConfig(level=logging.WARNING)
```

---

## Performance Tips

1. **Chunk Size**: Larger chunks = fewer API calls but may miss details
2. **Overlap**: More overlap = better context but higher cost
3. **Temperature**: Lower = more deterministic, higher = more creative
4. **Caching**: Consider caching section summaries for iterative refinement
5. **Parallel Processing**: Process multiple papers in parallel (with rate limiting)

---

## Version Information

API Version: 1.0.0  
Last Updated: January 30, 2026

For the latest updates, see README.md and CHANGELOG.md
