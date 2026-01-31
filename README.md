# Medical Research Paper Summarizer

A production-quality system for summarizing peer-reviewed medical research papers using Large Language Models (LLMs). Designed for accuracy, safety, and academic rigor.

## 🎯 Features

- **Multi-format Support**: PDF and PubMed Central XML
- **Intelligent Section Detection**: Automatically identifies Abstract, Methods, Results, Discussion, etc.
- **Map-Reduce Summarization**: Handles papers up to 40+ pages
- **Preserves Numerical Accuracy**: Exact replication of statistical results
- **Safety Controls**: Built-in safeguards against hallucination and medical advice
- **Structured Output**: JSON and Markdown formats
- **Modular Architecture**: Easy to extend and customize
- **LLM Flexibility**: Supports Claude (Anthropic) and GPT-4 (OpenAI)

## 📋 Requirements

- Python 3.10+
- API key for Anthropic (Claude) or OpenAI (GPT-4)

## 🚀 Quick Start

### Installation

```bash
# Clone repository
cd medical-paper-summarizer

# Install dependencies
pip install -r requirements.txt

# Download NLTK data (optional, for better sentence splitting)
python -c "import nltk; nltk.download('punkt')"

# Configure API keys
cp .env.example .env
# Edit .env and add your API keys
```

### Web UI (Full Site)

Launch the web interface:

```bash
python web_server.py
```

Then open http://localhost:8000 in your browser. Drop a PDF to get an AI-generated summary.

**Deploy as a live site:** See [DEPLOY.md](DEPLOY.md) for one-click deploy to Render, Railway, or Fly.io.

### Basic Usage (CLI)

```bash
# Summarize a PDF paper
python app.py paper.pdf

# Save as JSON
python app.py paper.pdf -o summary.json -f json

# Save as Markdown
python app.py paper.pdf -o summary.md -f markdown

# Use specific model
python app.py paper.pdf --model claude-sonnet-4-20250514

# Verbose output
python app.py paper.pdf -v
```

### Python API

```python
from summarization.summarizer import MedicalPaperSummarizer

# Initialize summarizer
summarizer = MedicalPaperSummarizer()

# Summarize paper
summary = summarizer.summarize("path/to/paper.pdf")

# Access structured data
print(summary.title)
print(summary.objective)
print(summary.key_findings)

# Export to markdown
markdown = summary.to_markdown()

# Export to JSON
json_str = summary.model_dump_json(indent=2)
```

## 🏗️ Architecture

### System Overview

```
Input (PDF/XML)
    ↓
Text Extraction & Cleaning
    ↓
Section Detection
    ↓
Chunking (800-1200 tokens, 150-250 overlap)
    ↓
Map-Reduce Summarization
    ├─ Map: Summarize each chunk
    └─ Reduce: Combine chunk summaries
    ↓
Structured Information Extraction
    ├─ Metadata (objective, study type, population)
    ├─ Methods summary
    ├─ Key findings
    ├─ Limitations
    └─ Conclusions
    ↓
Output (PaperSummary object → JSON/Markdown)
```

### Project Structure

```
medical-paper-summarizer/
│
├── ingestion/                  # Document loading
│   ├── pdf_loader.py          # PDF text extraction
│   ├── xml_loader.py          # PMC XML parsing
│   └── text_cleaner.py        # Text normalization
│
├── processing/                 # Text processing
│   ├── section_parser.py      # Section detection
│   └── chunker.py             # Text chunking
│
├── summarization/              # LLM orchestration
│   ├── prompts.py             # Prompt templates
│   ├── llm_client.py          # API client wrapper
│   ├── map_reduce.py          # Map-reduce logic
│   └── summarizer.py          # Main orchestrator
│
├── output/                     # Output schemas
│   └── schema.py              # Pydantic models
│
├── tests/                      # Test suite
│   └── test_components.py     # Unit tests
│
├── static/                     # Web UI assets
│   └── index.html             # Drag-and-drop interface
│
├── config.py                   # Configuration
├── app.py                      # CLI application
├── web_server.py               # Web UI server (FastAPI)
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

## 🔧 Configuration

Edit `.env` file or set environment variables:

```bash
# API Keys
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# Model Selection
PRIMARY_MODEL=claude-sonnet-4-20250514
FALLBACK_MODEL=gpt-4-turbo-preview
TEMPERATURE=0.2
MAX_TOKENS=4096

# Chunking
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_SECTION_CHUNKS=20

# Processing
MAX_RETRIES=3
TIMEOUT=60
RATE_LIMIT_DELAY=1.0
```

## 📊 Output Format

### JSON Schema

```json
{
  "title": "Paper title",
  "objective": "Primary research question",
  "study_type": "RCT | Meta-analysis | Cohort | etc.",
  "population": "Sample size and demographics",
  "methods": "Study design and procedures",
  "key_findings": [
    "Finding 1 with exact statistics",
    "Finding 2 with exact statistics"
  ],
  "limitations": [
    "Limitation 1",
    "Limitation 2"
  ],
  "author_conclusions": "Authors' stated conclusions",
  "keywords": ["keyword1", "keyword2"],
  "summary_timestamp": "2026-01-30T12:00:00",
  "model_used": "claude-sonnet-4-20250514",
  "safety_disclaimer": "This summary is for academic research purposes only..."
}
```

### Markdown Format

```markdown
# Paper Title

## Objective
Primary research question

## Study Design
**Type:** RCT
**Population:** 600 adults aged 40-75...

## Methods
Study design details...

## Key Findings
1. Finding with exact statistics
2. Another finding...

## Limitations
1. Limitation 1
2. Limitation 2

## Author Conclusions
Authors' conclusions...

## Keywords
keyword1, keyword2, keyword3

---
⚠️ This summary is for academic research purposes only...
```

## ⚠️ Safety Features

1. **No Hallucination**: Only extracts information explicitly stated in source text
2. **Numerical Accuracy**: Preserves all statistics exactly as reported
3. **No Medical Advice**: Explicitly forbidden from providing clinical guidance
4. **Author Conclusions Only**: Reports only what authors state, no interpretation
5. **Limitation Disclosure**: Always includes study limitations
6. **Safety Disclaimer**: All outputs include academic use disclaimer
7. **Low Temperature**: Uses temperature ≤ 0.3 for deterministic outputs

## 🧪 Testing

```bash
# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_components.py::TestPaperSummary -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## 🎓 Advanced Usage

### Custom Chunking

```python
from summarization.summarizer import MedicalPaperSummarizer

summarizer = MedicalPaperSummarizer(
    chunk_size=1200,      # Larger chunks
    chunk_overlap=250     # More overlap
)
```

### Model Selection

```python
# Use specific models
summarizer = MedicalPaperSummarizer(
    primary_model="claude-sonnet-4-20250514",
    fallback_model="gpt-4-turbo-preview"
)
```

### Section-Specific Processing

```python
from processing.section_parser import SectionParser
from processing.chunker import TextChunker

parser = SectionParser()
chunker = TextChunker()

# Parse document
sections = parser.parse(text)

# Process specific section
methods_section = sections['methods']
chunks = chunker.chunk(methods_section.content)
```

## 📝 Best Practices

1. **PDF Quality**: Use text-based PDFs, not scanned images
2. **Paper Length**: System handles up to 40 pages efficiently
3. **API Costs**: Monitor token usage for long papers
4. **Rate Limits**: Built-in delays prevent API throttling
5. **Validation**: Always validate numerical accuracy in output
6. **Clinical Use**: NEVER use for actual patient care decisions

## 🔍 Troubleshooting

### "No text extracted from PDF"
- PDF may be scanned image (use OCR first)
- Try `use_pymupdf=True` in PDFLoader

### "Section not detected"
- Paper may have non-standard structure
- Check section headers match expected patterns
- Manually specify sections if needed

### "API rate limit exceeded"
- Increase `RATE_LIMIT_DELAY` in config
- Reduce `CHUNK_SIZE` to make fewer API calls

### "Numerical values incorrect"
- Check source PDF text extraction quality
- Verify LLM temperature is ≤ 0.3
- Review prompt templates for clarity

## 🤝 Contributing

Contributions welcome! Please:

1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass

## 📄 License

MIT License - see LICENSE file for details

## ⚖️ Disclaimer

This tool is for academic research purposes only. It does NOT:
- Provide medical advice
- Replace professional medical judgment
- Guarantee accuracy for clinical decisions
- Constitute peer review or validation

Always consult original papers and domain experts for medical decisions.

## 📚 Citations

If you use this tool in research, please cite:

```
Medical Research Paper Summarizer
https://github.com/your-repo/medical-paper-summarizer
```

## 🙏 Acknowledgments

- Built with Claude 4 (Anthropic)
- Supports GPT-4 (OpenAI)
- Uses industry-standard libraries (pdfplumber, BeautifulSoup, Pydantic)

## 📧 Contact

For questions or issues, please open a GitHub issue.

---

**Version**: 1.0.0  
**Last Updated**: January 30, 2026
