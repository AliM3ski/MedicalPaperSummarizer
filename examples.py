"""
Example usage of Medical Paper Summarizer.

This script demonstrates various features and use cases.
"""
import logging
from pathlib import Path

from summarization.summarizer import MedicalPaperSummarizer, summarize_paper
from output.schema import PaperSummary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def example_basic_usage():
    """Example 1: Basic paper summarization."""
    print("\n" + "="*80)
    print("Example 1: Basic Usage")
    print("="*80 + "\n")
    
    # Initialize summarizer with defaults
    summarizer = MedicalPaperSummarizer()
    
    # Summarize a paper
    # summary = summarizer.summarize("path/to/paper.pdf")
    
    # Print results
    # print(f"Title: {summary.title}")
    # print(f"Study Type: {summary.study_type}")
    # print(f"\nKey Findings:")
    # for i, finding in enumerate(summary.key_findings, 1):
    #     print(f"{i}. {finding}")
    
    print("Note: Uncomment code and provide actual PDF path to run")


def example_custom_configuration():
    """Example 2: Custom configuration."""
    print("\n" + "="*80)
    print("Example 2: Custom Configuration")
    print("="*80 + "\n")
    
    # Initialize with custom settings
    summarizer = MedicalPaperSummarizer(
        primary_model="claude-sonnet-4-20250514",
        fallback_model="gpt-4-turbo-preview",
        chunk_size=1200,        # Larger chunks
        chunk_overlap=250       # More overlap for continuity
    )
    
    print(f"Configuration:")
    print(f"  Model: {summarizer.llm.primary_model}")
    print(f"  Chunk Size: {summarizer.chunker.chunk_size} tokens")
    print(f"  Chunk Overlap: {summarizer.chunker.chunk_overlap} tokens")


def example_output_formats():
    """Example 3: Different output formats."""
    print("\n" + "="*80)
    print("Example 3: Output Formats")
    print("="*80 + "\n")
    
    # Create example summary
    summary = PaperSummary(
        title="Example: Efficacy of Drug X in Type 2 Diabetes",
        study_type="Randomized Controlled Trial",
        population="600 adults aged 40-75 with HbA1c 7.5-10%",
        key_findings=[
            "HbA1c reduction: Drug X -1.2% vs placebo -0.3% (p<0.001)",
            "HbA1c <7%: Drug X 52% vs placebo 18%",
            "Similar adverse events (12% vs 10%)"
        ],
        limitations=[
            "24-week duration may not show long-term effects",
            "Predominantly White population"
        ],
        author_conclusions="Drug X significantly reduced HbA1c with similar safety profile",
        keywords=["type 2 diabetes", "hba1c", "rct", "drug x"],
        model_used="claude-sonnet-4-20250514"
    )
    
    # JSON output
    print("JSON Output:")
    print(summary.model_dump_json(indent=2)[:500] + "...")
    
    print("\n" + "-"*80 + "\n")
    
    # Markdown output
    print("Markdown Output:")
    print(summary.to_markdown()[:800] + "...")


def example_convenience_function():
    """Example 4: Using convenience function."""
    print("\n" + "="*80)
    print("Example 4: Convenience Function")
    print("="*80 + "\n")
    
    # Simple one-liner to summarize and save
    # summary = summarize_paper(
    #     file_path="path/to/paper.pdf",
    #     output_format="markdown",
    #     output_path="output/summary.md"
    # )
    
    print("Usage:")
    print("""
    summary = summarize_paper(
        file_path="paper.pdf",
        output_format="markdown",  # or "json"
        output_path="summary.md"
    )
    """)


def example_error_handling():
    """Example 5: Error handling."""
    print("\n" + "="*80)
    print("Example 5: Error Handling")
    print("="*80 + "\n")
    
    try:
        summarizer = MedicalPaperSummarizer()
        
        # Attempt to summarize non-existent file
        # summary = summarizer.summarize("nonexistent.pdf")
        
    except FileNotFoundError as e:
        print(f"File error: {e}")
    except ValueError as e:
        print(f"Processing error: {e}")
    except RuntimeError as e:
        print(f"LLM error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    print("\nAlways wrap summarization in try-except blocks for production use")


def example_section_analysis():
    """Example 6: Analyzing specific sections."""
    print("\n" + "="*80)
    print("Example 6: Section Analysis")
    print("="*80 + "\n")
    
    print("Code example for processing specific sections:")
    print("""
    from processing.section_parser import SectionParser
    from ingestion.pdf_loader import PDFLoader, TextCleaner
    
    # Load and parse
    loader = PDFLoader()
    cleaner = TextCleaner()
    parser = SectionParser()
    
    text = loader.load("paper.pdf")
    cleaned = cleaner.clean(text)
    sections = parser.parse(cleaned)
    
    # Analyze specific section
    if 'methods' in sections:
        methods = sections['methods']
        print(f"Methods section: {len(methods.content)} chars")
    
    # Get section order
    ordered = parser.get_section_order(sections)
    print(f"Sections in order: {ordered}")
    """)


def example_batch_processing():
    """Example 7: Batch processing multiple papers."""
    print("\n" + "="*80)
    print("Example 7: Batch Processing")
    print("="*80 + "\n")
    
    print("Code example for batch processing:")
    print("""
    import json
    from pathlib import Path
    
    # Initialize once
    summarizer = MedicalPaperSummarizer()
    
    # Process directory of papers
    papers_dir = Path("papers/")
    output_dir = Path("summaries/")
    output_dir.mkdir(exist_ok=True)
    
    for pdf_file in papers_dir.glob("*.pdf"):
        try:
            print(f"Processing {pdf_file.name}...")
            
            summary = summarizer.summarize(str(pdf_file))
            
            # Save as JSON
            output_file = output_dir / f"{pdf_file.stem}_summary.json"
            output_file.write_text(summary.model_dump_json(indent=2))
            
            print(f"  ✓ Saved to {output_file}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    """)


def main():
    """Run all examples."""
    print("\n" + "#"*80)
    print("# Medical Paper Summarizer - Examples")
    print("#"*80)
    
    example_basic_usage()
    example_custom_configuration()
    example_output_formats()
    example_convenience_function()
    example_error_handling()
    example_section_analysis()
    example_batch_processing()
    
    print("\n" + "="*80)
    print("Examples complete!")
    print("="*80 + "\n")
    print("To run with real papers:")
    print("1. Add API keys to .env file")
    print("2. Provide paths to actual PDF files")
    print("3. Uncomment example code")
    print("\n")


if __name__ == '__main__':
    main()
