"""
Tests for medical paper summarizer.
"""
import pytest
from pathlib import Path

from ingestion.pdf_loader import TextCleaner
from processing.section_parser import SectionParser, Section
from processing.chunker import TextChunker
from output.schema import PaperSummary


class TestTextCleaner:
    """Tests for TextCleaner."""
    
    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        cleaner = TextCleaner()
        text = "Hello    world\n\n\n\nNew  paragraph"
        cleaned = cleaner.clean(text)
        assert "    " not in cleaned
        assert "\n\n\n" not in cleaned
    
    def test_remove_references(self):
        """Test references section removal."""
        cleaner = TextCleaner()
        text = """
        Abstract text here.
        
        REFERENCES
        1. Author et al. Journal. 2020.
        2. Another author. 2021.
        """
        cleaned = cleaner.clean(text, remove_references=True)
        assert "REFERENCES" not in cleaned
        assert "Author et al" not in cleaned
    
    def test_remove_citations(self):
        """Test inline citation removal."""
        cleaner = TextCleaner()
        text = "This is a finding [1,2,3] from the study."
        cleaned = cleaner.clean(text, remove_citations=True)
        assert "[1,2,3]" not in cleaned
        assert "finding" in cleaned


class TestSectionParser:
    """Tests for SectionParser."""
    
    def test_parse_sections(self):
        """Test section parsing."""
        parser = SectionParser()
        text = """
        ABSTRACT
        This is the abstract.
        
        INTRODUCTION
        This is the introduction.
        
        METHODS
        This is the methods.
        
        RESULTS
        These are the results.
        
        DISCUSSION
        This is the discussion.
        """
        
        sections = parser.parse(text)
        
        assert 'abstract' in sections
        assert 'introduction' in sections
        assert 'methods' in sections
        assert 'results' in sections
        assert 'discussion' in sections
    
    def test_parse_numbered_sections(self):
        """Test section parsing with numbered headers (common in journals)."""
        parser = SectionParser()
        text = """
        Some intro text.

        1. Introduction
        This is the introduction.

        2. Materials and Methods
        This is the methods section.

        3. Results
        These are the results.

        4. Discussion
        This is the discussion.

        5. Conclusions
        This is the conclusion.
        """
        sections = parser.parse(text)
        assert 'introduction' in sections
        assert 'methods' in sections
        assert 'results' in sections
        assert 'discussion' in sections
        assert 'conclusion' in sections
        assert 'This is the introduction' in sections['introduction'].content
        assert '1. Introduction' not in sections['introduction'].content

    def test_validate_sections(self):
        """Test section validation."""
        parser = SectionParser()
        
        # Valid structure with abstract
        valid_sections = {
            'abstract': Section('abstract', 'text', 0, 10)
        }
        assert parser.validate_sections(valid_sections)
        
        # Valid structure with methods and results
        valid_sections2 = {
            'methods': Section('methods', 'text', 0, 10),
            'results': Section('results', 'text', 10, 20)
        }
        assert parser.validate_sections(valid_sections2)
        
        # Invalid structure (missing essential sections)
        invalid_sections = {
            'discussion': Section('discussion', 'text', 0, 10)
        }
        assert not parser.validate_sections(invalid_sections)


class TestTextChunker:
    """Tests for TextChunker."""
    
    def test_chunking(self):
        """Test text chunking."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        
        # Create long text (many sentences)
        sentences = [f"This is sentence number {i}." for i in range(50)]
        text = " ".join(sentences)
        
        chunks = chunker.chunk(text)
        
        assert len(chunks) > 1
        assert all(c.token_count <= 150 for c in chunks)  # Allow some margin
    
    def test_token_counting(self):
        """Test token counting."""
        chunker = TextChunker()
        
        text = "Hello world"
        count = chunker.count_tokens(text)
        
        assert count > 0
        assert isinstance(count, int)
    
    def test_truncate_to_tokens(self):
        """Test text truncation."""
        chunker = TextChunker()
        
        text = " ".join([f"word{i}" for i in range(1000)])
        truncated = chunker.truncate_to_tokens(text, 50)
        
        assert chunker.count_tokens(truncated) <= 50


class TestPaperSummary:
    """Tests for PaperSummary schema."""
    
    def test_valid_summary(self):
        """Test valid summary creation."""
        summary = PaperSummary(
            title="Test Paper",
            objective="Test objective",
            study_type="RCT",
            population="100 adults",
            methods="Double-blind trial",
            key_findings=["Finding 1", "Finding 2"],
            limitations=["Limitation 1"],
            author_conclusions="Significant results",
            keywords=["diabetes", "treatment"]
        )
        
        assert summary.title == "Test Paper"
        assert len(summary.key_findings) == 2
        assert len(summary.keywords) == 2
    
    def test_empty_findings_validation(self):
        """Test that empty findings raise validation error."""
        with pytest.raises(ValueError):
            PaperSummary(
                title="Test",
                objective="Test",
                study_type="RCT",
                population="100",
                methods="Test",
                key_findings=[],  # Empty findings
                author_conclusions="Test"
            )
    
    def test_keywords_deduplication(self):
        """Test keyword deduplication."""
        summary = PaperSummary(
            title="Test",
            objective="Test",
            study_type="RCT",
            population="100",
            methods="Test",
            key_findings=["Finding"],
            author_conclusions="Test",
            keywords=["diabetes", "Diabetes", "DIABETES", "treatment"]
        )
        
        # Should deduplicate to lowercase
        assert len(summary.keywords) == 2
        assert "diabetes" in summary.keywords
        assert "treatment" in summary.keywords
    
    def test_to_markdown(self):
        """Test markdown conversion."""
        summary = PaperSummary(
            title="Test Paper",
            objective="Test objective",
            study_type="RCT",
            population="100 adults",
            methods="Trial",
            key_findings=["Finding 1"],
            author_conclusions="Conclusions",
            keywords=["test"]
        )
        
        markdown = summary.to_markdown()
        
        assert "# Test Paper" in markdown
        assert "## Objective" in markdown
        assert "## Key Findings" in markdown
        assert "⚠️" in markdown  # Safety disclaimer


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
