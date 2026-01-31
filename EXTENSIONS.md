# Extension Guide

Guide for extending and customizing the Medical Paper Summarizer.

## Table of Contents

1. [Adding New Document Formats](#adding-new-document-formats)
2. [Custom Section Detection](#custom-section-detection)
3. [Custom Prompts](#custom-prompts)
4. [New LLM Providers](#new-llm-providers)
5. [Custom Output Formats](#custom-output-formats)
6. [Advanced Processing Pipelines](#advanced-processing-pipelines)

---

## Adding New Document Formats

### Example: Adding DOCX Support

1. Create new loader in `ingestion/`:

```python
# ingestion/docx_loader.py
from docx import Document
from typing import str

class DOCXLoader:
    """Extract text from DOCX files."""
    
    def load(self, docx_path: str) -> str:
        """Load text from DOCX."""
        doc = Document(docx_path)
        paragraphs = [p.text for p in doc.paragraphs]
        return '\n\n'.join(paragraphs)
    
    def get_metadata(self, docx_path: str) -> dict:
        """Extract DOCX metadata."""
        doc = Document(docx_path)
        return {
            'title': doc.core_properties.title,
            'author': doc.core_properties.author,
            'created': doc.core_properties.created
        }
```

2. Integrate into main summarizer:

```python
# summarization/summarizer.py
from ingestion.docx_loader import DOCXLoader

class MedicalPaperSummarizer:
    def __init__(self, ...):
        # ... existing code ...
        self.docx_loader = DOCXLoader()
    
    def _load_document(self, file_path: str) -> str:
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == '.pdf':
            return self.pdf_loader.load(file_path)
        elif suffix == '.xml':
            return self.xml_loader.load(file_path)
        elif suffix == '.docx':  # New format
            return self.docx_loader.load(file_path)
        else:
            raise ValueError(f"Unsupported format: {suffix}")
```

---

## Custom Section Detection

### Example: Adding Journal-Specific Sections

```python
# processing/custom_parser.py
from processing.section_parser import SectionParser

class CustomJournalParser(SectionParser):
    """Parser for specific journal format."""
    
    def __init__(self):
        super().__init__()
        
        # Add custom section patterns
        self.HEADER_PATTERNS.update({
            'statistical_analysis': [
                r'\bSTATISTICAL ANALYSIS\b',
                r'\bDATA ANALYSIS\b'
            ],
            'funding': [
                r'\bFUNDING\b',
                r'\bFINANCIAL SUPPORT\b'
            ],
            'ethics': [
                r'\bETHICS STATEMENT\b',
                r'\bETHICAL APPROVAL\b'
            ]
        })
```

Usage:

```python
from processing.custom_parser import CustomJournalParser

parser = CustomJournalParser()
sections = parser.parse(text)
```

---

## Custom Prompts

### Example: Domain-Specific Prompts

Create custom prompt set for specific medical domain:

```python
# summarization/custom_prompts.py
from summarization.prompts import PromptTemplates

class CardiologyPrompts(PromptTemplates):
    """Prompts optimized for cardiology papers."""
    
    FINDINGS_PROMPT = """Extract cardiovascular findings from results section.

FOCUS ON:
- Cardiac outcomes (MACE, mortality, heart failure)
- Hemodynamic measurements (BP, HR, ejection fraction)
- Intervention effects on cardiovascular endpoints
- Adverse cardiac events

RESULTS:
{results_text}

KEY FINDINGS (JSON array with exact values):
[...]
"""
    
    METHODS_PROMPT = """Summarize cardiology study methods.

INCLUDE:
- Study design and duration
- Cardiac intervention details
- Primary cardiac endpoints
- Imaging/diagnostic procedures
- Cardiovascular risk stratification

METHODS:
{methods_text}

METHODS SUMMARY:
"""
```

Usage:

```python
# Replace default prompts
from summarization import prompts
from summarization.custom_prompts import CardiologyPrompts

prompts.PromptTemplates = CardiologyPrompts
```

---

## New LLM Providers

### Example: Adding Cohere Support

```python
# summarization/llm_client.py
import cohere
from enum import Enum

class ModelProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    COHERE = "cohere"  # New provider

class LLMClient:
    def __init__(self, ...):
        # ... existing code ...
        self.cohere_client = None
        
        if settings.cohere_api_key:
            self.cohere_client = cohere.Client(
                api_key=settings.cohere_api_key
            )
    
    def _get_provider(self, model: str) -> ModelProvider:
        if model.startswith("claude"):
            return ModelProvider.ANTHROPIC
        elif model.startswith("gpt"):
            return ModelProvider.OPENAI
        elif model.startswith("command"):  # Cohere models
            return ModelProvider.COHERE
        else:
            raise ValueError(f"Unknown model: {model}")
    
    def _call_cohere(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Call Cohere API."""
        if not self.cohere_client:
            raise RuntimeError("Cohere client not initialized")
        
        # Combine prompts
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        response = self.cohere_client.generate(
            model=model,
            prompt=full_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.generations[0].text
```

---

## Custom Output Formats

### Example: Adding LaTeX Output

```python
# output/latex_formatter.py
from output.schema import PaperSummary

class LaTeXFormatter:
    """Convert summary to LaTeX format."""
    
    @staticmethod
    def format(summary: PaperSummary) -> str:
        """Convert to LaTeX."""
        latex = r"""\documentclass{article}
\usepackage[utf8]{inputenc}

\title{""" + summary.title + r"""}
\author{Generated Summary}
\date{""" + summary.summary_timestamp.strftime("%Y-%m-%d") + r"""}

\begin{document}

\maketitle

\section{Objective}
""" + summary.objective + r"""

\section{Study Design}
\textbf{Type:} """ + summary.study_type + r"""

\textbf{Population:} """ + summary.population + r"""

\section{Methods}
""" + summary.methods + r"""

\section{Key Findings}
\begin{enumerate}
"""
        for finding in summary.key_findings:
            latex += f"\\item {finding}\n"
        
        latex += r"""\end{enumerate}

\section{Limitations}
\begin{itemize}
"""
        for limitation in summary.limitations:
            latex += f"\\item {limitation}\n"
        
        latex += r"""\end{itemize}

\section{Author Conclusions}
""" + summary.author_conclusions + r"""

\section{Keywords}
""" + ", ".join(summary.keywords) + r"""

\end{document}
"""
        return latex
```

Usage:

```python
from output.latex_formatter import LaTeXFormatter

summary = summarizer.summarize("paper.pdf")
latex = LaTeXFormatter.format(summary)

with open("summary.tex", "w") as f:
    f.write(latex)
```

---

## Advanced Processing Pipelines

### Example: Multi-Stage Refinement

```python
# summarization/refinement_pipeline.py
from summarization.summarizer import MedicalPaperSummarizer
from output.schema import PaperSummary

class RefinementPipeline:
    """Multi-stage summary refinement."""
    
    def __init__(self):
        self.summarizer = MedicalPaperSummarizer()
    
    def process(self, file_path: str) -> PaperSummary:
        """Process with refinement."""
        # Stage 1: Initial summary
        summary = self.summarizer.summarize(file_path)
        
        # Stage 2: Verify numerical accuracy
        summary = self._verify_numbers(summary, file_path)
        
        # Stage 3: Enhance limitations
        summary = self._enhance_limitations(summary)
        
        # Stage 4: Quality check
        self._quality_check(summary)
        
        return summary
    
    def _verify_numbers(
        self,
        summary: PaperSummary,
        file_path: str
    ) -> PaperSummary:
        """Cross-check numerical values."""
        # Extract all numbers from findings
        import re
        
        numbers = []
        for finding in summary.key_findings:
            nums = re.findall(r'\d+\.?\d*', finding)
            numbers.extend(nums)
        
        # Verify against original text
        # (Implementation would check original paper)
        
        return summary
    
    def _enhance_limitations(
        self,
        summary: PaperSummary
    ) -> PaperSummary:
        """Add common methodological limitations."""
        # Use LLM to identify implicit limitations
        
        prompt = f"""Given this study design:
        
Study Type: {summary.study_type}
Population: {summary.population}
Methods: {summary.methods}

Stated Limitations: {summary.limitations}

Are there common methodological limitations not mentioned?
(e.g., selection bias, confounding, generalizability)

Respond with JSON array of additional limitations:
[...]
"""
        
        # Call LLM and merge limitations
        # (Implementation details)
        
        return summary
    
    def _quality_check(self, summary: PaperSummary):
        """Validate summary quality."""
        checks = []
        
        # Check 1: Has findings
        if not summary.key_findings:
            checks.append("No key findings")
        
        # Check 2: Findings have numbers
        has_numbers = any(
            any(char.isdigit() for char in finding)
            for finding in summary.key_findings
        )
        if not has_numbers:
            checks.append("Findings lack numerical data")
        
        # Check 3: Has limitations
        if not summary.limitations:
            checks.append("No limitations mentioned")
        
        if checks:
            raise ValueError(f"Quality checks failed: {', '.join(checks)}")
```

---

## Plugin Architecture

### Example: Plugin System

```python
# plugins/base.py
from abc import ABC, abstractmethod
from output.schema import PaperSummary

class SummarizerPlugin(ABC):
    """Base class for plugins."""
    
    @abstractmethod
    def process(self, summary: PaperSummary) -> PaperSummary:
        """Process summary."""
        pass

# plugins/citation_checker.py
class CitationCheckerPlugin(SummarizerPlugin):
    """Check that claims are properly supported."""
    
    def process(self, summary: PaperSummary) -> PaperSummary:
        # Verify each finding can be traced to source
        return summary

# Usage
plugins = [
    CitationCheckerPlugin(),
    # ... other plugins
]

summary = summarizer.summarize("paper.pdf")
for plugin in plugins:
    summary = plugin.process(summary)
```

---

## Best Practices for Extensions

1. **Maintain Type Hints**: Keep code well-typed for IDE support
2. **Add Tests**: Create tests for new functionality
3. **Document**: Add docstrings and examples
4. **Error Handling**: Include proper error handling
5. **Logging**: Add logging for debugging
6. **Configuration**: Make extensions configurable
7. **Backward Compatibility**: Don't break existing functionality

---

## Contributing Guidelines

When contributing extensions:

1. Follow existing code structure
2. Add comprehensive tests
3. Update documentation
4. Include usage examples
5. Consider performance impact
6. Maintain safety features

---

## Support

For questions about extending the system:
1. Check API.md for implementation details
2. Review existing code for patterns
3. Open GitHub issue for guidance
