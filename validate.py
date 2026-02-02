#!/usr/bin/env python3
"""
System validation and health check script.

Run this to verify installation and configuration.
"""
import sys
from pathlib import Path
import importlib.util


def check_python_version():
    """Check Python version."""
    major, minor = sys.version_info[:2]
    required_major, required_minor = 3, 10
    
    if (major, minor) >= (required_major, required_minor):
        print(f"✓ Python {major}.{minor} (>= {required_major}.{required_minor})")
        return True
    else:
        print(f"✗ Python {major}.{minor} (requires >= {required_major}.{required_minor})")
        return False


def check_dependencies():
    """Check required packages."""
    required = [
        'anthropic',
        'openai',
        'pdfplumber',
        'fitz',  # PyMuPDF
        'bs4',  # beautifulsoup4
        'tiktoken',
        'pydantic',
        'dotenv'
    ]
    
    missing = []
    for package in required:
        spec = importlib.util.find_spec(package)
        if spec is None:
            missing.append(package)
            print(f"✗ {package}: NOT FOUND")
        else:
            print(f"✓ {package}: installed")
    
    return len(missing) == 0


def check_config():
    """Check configuration."""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("✗ .env file not found")
        print("  Run: cp .env.example .env")
        return False
    
    print("✓ .env file exists")
    
    # Try to load config
    try:
        from config import settings
        
        has_anthropic = bool(settings.anthropic_api_key)
        has_openai = bool(settings.openai_api_key)
        
        if has_anthropic:
            print("✓ Anthropic API key configured")
        else:
            print("✗ Anthropic API key not set")
        
        if has_openai:
            print("✓ OpenAI API key configured")
        else:
            print("✗ OpenAI API key not set")
        
        if not (has_anthropic or has_openai):
            print("✗ No API keys configured")
            return False
        
        print(f"✓ Primary model: {settings.primary_model}")
        print(f"✓ Chunk size: {settings.chunk_size}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        return False


def check_structure():
    """Check project structure."""
    required_dirs = [
        'ingestion',
        'processing',
        'summarization',
        'output',
        'tests'
    ]
    
    required_files = [
        'config.py',
        'app.py',
        'requirements.txt',
        'README.md'
    ]
    
    all_good = True
    
    for dirname in required_dirs:
        path = Path(dirname)
        if path.exists() and path.is_dir():
            print(f"✓ {dirname}/ directory")
        else:
            print(f"✗ {dirname}/ directory missing")
            all_good = False
    
    for filename in required_files:
        path = Path(filename)
        if path.exists():
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename} missing")
            all_good = False
    
    return all_good


def check_imports():
    """Test importing main modules."""
    modules = [
        'config',
        'ingestion.pdf_loader',
        'ingestion.xml_loader',
        'processing.section_parser',
        'processing.chunker',
        'summarization.llm_client',
        'summarization.summarizer',
        'output.schema'
    ]
    
    all_good = True
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"✓ Import {module}")
        except Exception as e:
            print(f"✗ Import {module}: {e}")
            all_good = False
    
    return all_good


def run_basic_test():
    """Run basic functionality test."""
    try:
        from output.schema import PaperSummary
        
        # Create test summary
        summary = PaperSummary(
            title="Test Paper",
            study_type="Test study",
            population="Test population",
            key_findings=["Finding 1", "Finding 2"],
            author_conclusions="Test conclusions",
            keywords=["test"]
        )
        
        # Test JSON export
        json_str = summary.model_dump_json()
        assert len(json_str) > 0
        
        # Test markdown export
        md_str = summary.to_markdown()
        assert "# Test Paper" in md_str
        
        print("✓ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False


def main():
    """Run all checks."""
    print("="*80)
    print("Medical Paper Summarizer - System Validation")
    print("="*80 + "\n")
    
    print("Checking Python version...")
    py_ok = check_python_version()
    print()
    
    print("Checking dependencies...")
    deps_ok = check_dependencies()
    print()
    
    print("Checking configuration...")
    config_ok = check_config()
    print()
    
    print("Checking project structure...")
    struct_ok = check_structure()
    print()
    
    print("Checking module imports...")
    imports_ok = check_imports()
    print()
    
    print("Running basic tests...")
    test_ok = run_basic_test()
    print()
    
    print("="*80)
    print("Summary:")
    print("="*80)
    
    checks = [
        ("Python version", py_ok),
        ("Dependencies", deps_ok),
        ("Configuration", config_ok),
        ("Project structure", struct_ok),
        ("Module imports", imports_ok),
        ("Basic tests", test_ok)
    ]
    
    for name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    
    if all(result for _, result in checks):
        print("✓ All checks passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Try: python examples.py")
        print("2. Process a paper: python app.py path/to/paper.pdf")
        return 0
    else:
        print("✗ Some checks failed. Please address the issues above.")
        print("\nCommon fixes:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Configure API keys: cp .env.example .env (then edit)")
        print("3. Check Python version: python --version")
        return 1


if __name__ == '__main__':
    sys.exit(main())
