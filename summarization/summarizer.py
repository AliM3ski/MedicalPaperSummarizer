"""
Main paper summarizer orchestrator.
"""
from pathlib import Path
from typing import Optional, Union
import logging

from ingestion.pdf_loader import PDFLoader, TextCleaner
from ingestion.xml_loader import XMLLoader
from processing.section_parser import SectionParser
from processing.chunker import TextChunker
from summarization.llm_client import LLMClient
from summarization.map_reduce import MapReduceSummarizer
from summarization import prompts
from output.schema import PaperSummary
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MedicalPaperSummarizer:
    """Main orchestrator for medical paper summarization."""
    
    def __init__(
        self,
        primary_model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        """
        Initialize summarizer.
        
        Args:
            primary_model: Primary LLM model
            fallback_model: Fallback LLM model
            chunk_size: Text chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
        """
        # Initialize components
        self.pdf_loader = PDFLoader(use_pymupdf=True)
        self.xml_loader = XMLLoader()
        self.text_cleaner = TextCleaner()
        self.section_parser = SectionParser()
        
        self.chunker = TextChunker(
            chunk_size=chunk_size or settings.chunk_size,
            chunk_overlap=chunk_overlap or settings.chunk_overlap
        )
        
        self.llm = LLMClient(
            primary_model=primary_model,
            fallback_model=fallback_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens
        )
        
        self.map_reduce = MapReduceSummarizer(
            llm_client=self.llm,
            chunker=self.chunker
        )
    
    def summarize(
        self,
        file_path: str,
        title: Optional[str] = None
    ) -> PaperSummary:
        """
        Summarize a medical research paper.
        
        Args:
            file_path: Path to PDF or XML file
            title: Optional paper title (auto-extracted if not provided)
            
        Returns:
            PaperSummary object
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is unsupported or processing fails
        """
        logger.info(f"Starting summarization of: {file_path}")
        
        # Step 1: Load document
        text = self._load_document(file_path)
        logger.info(f"Loaded document: {len(text)} characters")
        
        # Step 2: Clean text
        cleaned_text = self.text_cleaner.clean(
            text,
            remove_references=True,
            remove_figures_tables=True,
            remove_citations=False  # Keep citations for context
        )
        logger.info(f"Cleaned text: {len(cleaned_text)} characters")
        
        # Step 3: Parse sections
        sections = self.section_parser.parse(cleaned_text)
        logger.info(f"Detected {len(sections)} sections: {list(sections.keys())}")
        
        # Validate section structure
        if not self.section_parser.validate_sections(sections):
            logger.warning("Document structure may be incomplete")
        
        # Step 4: Summarize sections using map-reduce
        logger.info("Starting section summarization...")
        section_summaries = self.map_reduce.summarize_all_sections(sections)
        
        # Step 5: Extract structured information
        logger.info("Extracting structured information...")
        preamble = self._get_preamble(cleaned_text, sections)
        structured_info = self.map_reduce.extract_structured_info(
            sections,
            section_summaries,
            preamble=preamble
        )
        
        # Step 6: Extract title if not provided
        if not title:
            title = self.text_cleaner.extract_title(cleaned_text)
            if not title:
                title = "Untitled Paper"
        
        # Step 7: Extract keywords
        keywords = self._extract_keywords(cleaned_text)
        
        # Step 8: Build final summary
        summary = PaperSummary(
            title=title,
            objective=structured_info.get('objective', ''),
            study_type=structured_info.get('study_type', ''),
            population=structured_info.get('population', ''),
            methods=structured_info.get('methods', ''),
            key_findings=structured_info.get('key_findings', []),
            limitations=structured_info.get('limitations', []),
            author_conclusions=structured_info.get('author_conclusions', ''),
            keywords=keywords,
            model_used=self.llm.primary_model
        )
        
        logger.info("Summarization complete!")
        return summary
    
    def _load_document(self, file_path: str) -> str:
        """
        Load document from PDF or XML.
        
        Args:
            file_path: Path to file
            
        Returns:
            Extracted text
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If format is unsupported
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == '.pdf':
            return self.pdf_loader.load(file_path)
        elif suffix == '.xml':
            return self.xml_loader.load(file_path)
        else:
            raise ValueError(
                f"Unsupported file format: {suffix}. "
                "Supported formats: .pdf, .xml"
            )
    
    def _get_preamble(self, cleaned_text: str, sections: dict) -> str:
        """Get text before first section (often contains abstract for numbered-format papers)."""
        if not sections or 'full_text' in sections:
            return ""
        first_start = min(s.start_index for s in sections.values())
        if first_start <= 0:
            return ""
        preamble = cleaned_text[:first_start].strip()
        return self.chunker.truncate_to_tokens(preamble, 1500)
    
    def _extract_keywords(self, text: str, max_tokens: int = 2000) -> list:
        """
        Extract keywords from paper.
        
        Args:
            text: Paper text
            max_tokens: Maximum tokens to analyze
            
        Returns:
            List of keywords
        """
        # Use first part of text for keyword extraction
        truncated = self.chunker.truncate_to_tokens(text, max_tokens)
        
        try:
            prompt = prompts.get_keywords_prompt(truncated)
            
            response = self.llm.complete(
                prompt=prompt,
                system_prompt=prompts.PromptTemplates.SYSTEM_PROMPT,
                temperature=0.1,
                json_mode=True
            )
            
            keywords = self.llm.parse_json_response(response)
            
            if isinstance(keywords, list):
                return keywords
            else:
                return []
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def get_processing_stats(self) -> dict:
        """
        Get statistics about last processing run.
        
        Returns:
            Dictionary with statistics
        """
        # This could be enhanced to track detailed stats during processing
        return {
            'model': self.llm.primary_model,
            'chunk_size': self.chunker.chunk_size,
            'chunk_overlap': self.chunker.chunk_overlap
        }


def summarize_paper(
    file_path: str,
    output_format: str = "json",
    output_path: Optional[str] = None
) -> Union[PaperSummary, str]:
    """
    Convenience function to summarize a paper.
    
    Args:
        file_path: Path to PDF or XML file
        output_format: Output format ('json', 'markdown', or 'object')
        output_path: Optional path to save output
        
    Returns:
        PaperSummary object, JSON string, or markdown string
    """
    summarizer = MedicalPaperSummarizer()
    summary = summarizer.summarize(file_path)
    
    # Format output
    if output_format == "json":
        output = summary.model_dump_json(indent=2)
    elif output_format == "markdown":
        output = summary.to_markdown()
    else:
        output = summary
    
    # Save if path provided
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(output, str):
            path.write_text(output, encoding='utf-8')
        else:
            path.write_text(summary.model_dump_json(indent=2), encoding='utf-8')
        
        logger.info(f"Summary saved to: {output_path}")
    
    return output
