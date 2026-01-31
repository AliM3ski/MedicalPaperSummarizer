#!/usr/bin/env python3
"""
Medical Research Paper Summarizer - Command Line Interface
"""
import argparse
import sys
import logging
from pathlib import Path

from summarization.summarizer import MedicalPaperSummarizer
from config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Summarize medical research papers using LLMs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Summarize a PDF paper
  python app.py paper.pdf
  
  # Summarize and save as JSON
  python app.py paper.pdf -o summary.json -f json
  
  # Summarize and save as Markdown
  python app.py paper.pdf -o summary.md -f markdown
  
  # Use specific model
  python app.py paper.pdf --model claude-sonnet-4-20250514
  
  # Adjust chunking parameters
  python app.py paper.pdf --chunk-size 1200 --chunk-overlap 250
        """
    )
    
    parser.add_argument(
        'input_file',
        type=str,
        help='Path to PDF or XML file to summarize'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output file path (optional)'
    )
    
    parser.add_argument(
        '-f', '--format',
        type=str,
        choices=['json', 'markdown'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help=f'LLM model to use (default: {settings.primary_model})'
    )
    
    parser.add_argument(
        '--fallback-model',
        type=str,
        default=None,
        help=f'Fallback model (default: {settings.fallback_model})'
    )
    
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=None,
        help=f'Chunk size in tokens (default: {settings.chunk_size})'
    )
    
    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=None,
        help=f'Chunk overlap in tokens (default: {settings.chunk_overlap})'
    )
    
    parser.add_argument(
        '--title',
        type=str,
        default=None,
        help='Paper title (auto-extracted if not provided)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input_file}")
        sys.exit(1)
    
    if input_path.suffix.lower() not in ['.pdf', '.xml']:
        logger.error(f"Unsupported file format: {input_path.suffix}")
        logger.error("Supported formats: .pdf, .xml")
        sys.exit(1)
    
    # Check API keys
    if not settings.anthropic_api_key and not settings.openai_api_key:
        logger.error("No API keys configured!")
        logger.error("Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env file")
        sys.exit(1)
    
    try:
        # Initialize summarizer
        logger.info("Initializing summarizer...")
        summarizer = MedicalPaperSummarizer(
            primary_model=args.model,
            fallback_model=args.fallback_model,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap
        )
        
        # Summarize
        logger.info(f"Processing: {args.input_file}")
        summary = summarizer.summarize(
            file_path=args.input_file,
            title=args.title
        )
        
        # Format output
        if args.format == 'json':
            output_text = summary.model_dump_json(indent=2)
        else:
            output_text = summary.to_markdown()
        
        # Save or print
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output_text, encoding='utf-8')
            logger.info(f"Summary saved to: {args.output}")
        else:
            print("\n" + "="*80)
            print("SUMMARY")
            print("="*80 + "\n")
            print(output_text)
        
        logger.info("✓ Summarization complete!")
        
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == '__main__':
    main()
