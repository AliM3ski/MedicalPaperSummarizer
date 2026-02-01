"""
PDF document loader and text extractor.
"""
import pdfplumber
import fitz  # PyMuPDF
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PDFLoader:
    """Extract text from PDF research papers."""
    
    def __init__(self, use_pymupdf: bool = False):
        """
        Initialize PDF loader.
        
        Args:
            use_pymupdf: Use PyMuPDF instead of pdfplumber (faster but less accurate)
        """
        self.use_pymupdf = use_pymupdf
    
    def load(self, pdf_path: str) -> str:
        """
        Load and extract text from PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
            
        Raises:
            FileNotFoundError: If PDF doesn't exist
            ValueError: If PDF is corrupted or unreadable
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        try:
            if self.use_pymupdf:
                return self._extract_with_pymupdf(pdf_path)
            else:
                return self._extract_with_pdfplumber(pdf_path)
        except Exception as e:
            logger.error(f"Error extracting PDF {pdf_path}: {e}")
            raise ValueError(f"Failed to extract PDF: {e}")
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """Extract text using pdfplumber (more accurate)."""
        text_parts = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num}: {e}")
                    continue
        
        if not text_parts:
            raise ValueError("No text extracted from PDF")
        
        return "\n\n".join(text_parts)
    
    def _extract_with_pymupdf(self, pdf_path: str) -> str:
        """Extract text using PyMuPDF (faster)."""
        text_parts = []
        
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            try:
                page = doc[page_num]
                page_text = page.get_text()
                if page_text:
                    text_parts.append(page_text)
            except Exception as e:
                logger.warning(f"Error extracting page {page_num + 1}: {e}")
                continue
        
        doc.close()
        
        if not text_parts:
            raise ValueError("No text extracted from PDF")
        
        return "\n\n".join(text_parts)
    
    def get_metadata(self, pdf_path: str) -> Dict[str, any]:
        """
        Extract PDF metadata.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with metadata (title, author, creation date, etc.)
        """
        metadata = {}
        
        try:
            if self.use_pymupdf:
                doc = fitz.open(pdf_path)
                metadata = doc.metadata or {}
                metadata["page_count"] = len(doc)
                doc.close()
            else:
                with pdfplumber.open(pdf_path) as pdf:
                    metadata = pdf.metadata or {}
                    metadata["page_count"] = len(pdf.pages)
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")
        
        return metadata


class TextCleaner:
    """Clean and normalize extracted text."""
    
    # Patterns for content to remove
    REFERENCE_PATTERNS = [
        r'\n\s*REFERENCES\s*\n.*',
        r'\n\s*References\s*\n.*',
        r'\n\s*Bibliography\s*\n.*',
    ]
    
    FIGURE_TABLE_PATTERNS = [
        r'Figure\s+\d+[.:][^\n]+',
        r'Table\s+\d+[.:][^\n]+',
        r'\(Fig\.\s+\d+\)',
        r'\(Table\s+\d+\)',
    ]
    
    CITATION_PATTERNS = [
        r'\[\d+(?:,\s*\d+)*\]',  # [1], [1,2,3]
        r'\(\w+\s+et\s+al\.,?\s+\d{4}\)',  # (Author et al., 2020)
    ]
    
    def clean(self, text: str, remove_references: bool = True,
              remove_figures_tables: bool = True,
              remove_citations: bool = False) -> str:
        """
        Clean extracted text.
        
        Args:
            text: Raw extracted text
            remove_references: Remove references section
            remove_figures_tables: Remove figure/table captions
            remove_citations: Remove inline citations
            
        Returns:
            Cleaned text
        """
        cleaned = text
        
        # Remove references section
        if remove_references:
            for pattern in self.REFERENCE_PATTERNS:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove figure and table captions
        if remove_figures_tables:
            for pattern in self.FIGURE_TABLE_PATTERNS:
                cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Remove inline citations
        if remove_citations:
            for pattern in self.CITATION_PATTERNS:
                cleaned = re.sub(pattern, '', cleaned)
        
        # Normalize whitespace
        cleaned = self._normalize_whitespace(cleaned)
        
        # Remove page numbers and headers/footers (heuristic)
        cleaned = self._remove_page_artifacts(cleaned)
        
        return cleaned.strip()
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace and line breaks."""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove trailing whitespace from lines
        text = '\n'.join(line.rstrip() for line in text.split('\n'))
        
        return text
    
    def _remove_page_artifacts(self, text: str) -> str:
        """Remove page numbers and repeated headers/footers."""
        lines = text.split('\n')
        
        # Remove lines that are just page numbers
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip if line is just a number (page number)
            if stripped.isdigit() and len(stripped) <= 3:
                continue
            # Skip very short lines at document boundaries (likely headers/footers)
            if len(stripped) < 10 and (not cleaned_lines or not cleaned_lines[-1]):
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def extract_title(self, text: str) -> Optional[str]:
        """
        Attempt to extract paper title from beginning of text.
        
        Args:
            text: Cleaned text
            
        Returns:
            Extracted title or None
        """
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if not lines:
            return None
        
        # Patterns that indicate non-title lines
        skip_patterns = [
            r'^(author|doi|published|volume|issue|pages?|correspondence|received|accepted|copyright)[:|\s]',
            r'^[\d\s\.\-]+$',  # Just numbers
        ]
        # Author line: "Name,1 Name2,2" - comma followed by superscript number
        author_pattern = re.compile(r',\s*\d+\s|,\d+[,\s]')
        
        def is_author_line(line: str) -> bool:
            return bool(author_pattern.search(line)) or len(re.findall(r',\d+', line)) >= 2
        
        def is_metadata_line(line: str) -> bool:
            lower = line.lower()
            if len(line) < 15:
                return True
            for pat in skip_patterns:
                if re.match(pat, line, re.IGNORECASE):
                    return True
            if any(kw in lower for kw in ['department', 'university', 'hospital', 'institute', '@']):
                return True
            return False
        
        # Collect title lines (typically 1-3 lines before authors)
        title_lines = []
        for line in lines[:12]:
            if is_author_line(line) or is_metadata_line(line):
                if title_lines:
                    break
                continue
            if line.lower() in ('research article', 'original article', 'brief report'):
                continue
            title_lines.append(line)
            if len(title_lines) >= 3:
                break
        
        if not title_lines:
            return lines[0] if lines else None
        
        # Join if multi-line title (common when title wraps)
        title = ' '.join(title_lines)
        return title if len(title) > 10 else (title_lines[0] or None)
