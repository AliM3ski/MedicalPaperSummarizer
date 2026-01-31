"""
XML document loader for PubMed Central articles.
"""
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class XMLLoader:
    """Extract text from PubMed Central XML files."""
    
    def load(self, xml_path: str) -> str:
        """
        Load and extract text from PMC XML.
        
        Args:
            xml_path: Path to XML file
            
        Returns:
            Extracted text with section structure
            
        Raises:
            FileNotFoundError: If XML doesn't exist
            ValueError: If XML is malformed
        """
        path = Path(xml_path)
        if not path.exists():
            raise FileNotFoundError(f"XML not found: {xml_path}")
        
        try:
            with open(xml_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'lxml-xml')
            
            return self._extract_structured_text(soup)
        except Exception as e:
            logger.error(f"Error parsing XML {xml_path}: {e}")
            raise ValueError(f"Failed to parse XML: {e}")
    
    def _extract_structured_text(self, soup: BeautifulSoup) -> str:
        """Extract text preserving section structure."""
        parts = []
        
        # Extract title
        title = self._extract_title(soup)
        if title:
            parts.append(f"TITLE: {title}\n")
        
        # Extract abstract
        abstract = self._extract_abstract(soup)
        if abstract:
            parts.append(f"ABSTRACT\n{abstract}\n")
        
        # Extract body sections
        body_text = self._extract_body(soup)
        if body_text:
            parts.append(body_text)
        
        return "\n\n".join(parts)
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title."""
        # Try article-title first
        title_tag = soup.find('article-title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        # Fallback to title-group
        title_group = soup.find('title-group')
        if title_group:
            return title_group.get_text(strip=True)
        
        return None
    
    def _extract_abstract(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract abstract."""
        abstract_tag = soup.find('abstract')
        if not abstract_tag:
            return None
        
        # Handle structured abstracts
        sections = abstract_tag.find_all('sec')
        if sections:
            abstract_parts = []
            for sec in sections:
                title = sec.find('title')
                if title:
                    abstract_parts.append(f"{title.get_text(strip=True)}: ")
                
                # Get text excluding nested tags
                for title in sec.find_all('title'):
                    title.decompose()
                
                abstract_parts.append(sec.get_text(strip=True))
            
            return ' '.join(abstract_parts)
        else:
            # Unstructured abstract
            return abstract_tag.get_text(strip=True)
    
    def _extract_body(self, soup: BeautifulSoup) -> str:
        """Extract body with section headers."""
        body = soup.find('body')
        if not body:
            return ""
        
        parts = []
        sections = body.find_all('sec', recursive=False)
        
        for sec in sections:
            section_text = self._extract_section(sec)
            if section_text:
                parts.append(section_text)
        
        return "\n\n".join(parts)
    
    def _extract_section(self, section_tag, level: int = 1) -> str:
        """Recursively extract section with subsections."""
        parts = []
        
        # Get section title
        title_tag = section_tag.find('title', recursive=False)
        if title_tag:
            title = title_tag.get_text(strip=True).upper()
            parts.append(f"{title}\n")
            title_tag.decompose()  # Remove from tree
        
        # Get section paragraphs (non-recursive)
        paragraphs = section_tag.find_all('p', recursive=False)
        for p in paragraphs:
            # Remove references, figures, tables
            for unwanted in p.find_all(['xref', 'fig', 'table-wrap']):
                unwanted.decompose()
            
            text = p.get_text(strip=True)
            if text:
                parts.append(text)
        
        # Get subsections
        subsections = section_tag.find_all('sec', recursive=False)
        for subsec in subsections:
            subsec_text = self._extract_section(subsec, level + 1)
            if subsec_text:
                parts.append(subsec_text)
        
        return '\n'.join(parts)
    
    def get_metadata(self, xml_path: str) -> Dict[str, any]:
        """
        Extract article metadata.
        
        Args:
            xml_path: Path to XML file
            
        Returns:
            Dictionary with metadata
        """
        metadata = {}
        
        try:
            with open(xml_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'lxml-xml')
            
            # Title
            metadata['title'] = self._extract_title(soup)
            
            # Authors
            metadata['authors'] = self._extract_authors(soup)
            
            # Journal
            journal = soup.find('journal-title')
            if journal:
                metadata['journal'] = journal.get_text(strip=True)
            
            # Publication date
            pub_date = soup.find('pub-date')
            if pub_date:
                year = pub_date.find('year')
                month = pub_date.find('month')
                day = pub_date.find('day')
                
                date_parts = []
                if year:
                    date_parts.append(year.get_text(strip=True))
                if month:
                    date_parts.append(month.get_text(strip=True))
                if day:
                    date_parts.append(day.get_text(strip=True))
                
                metadata['publication_date'] = '-'.join(date_parts)
            
            # DOI
            doi = soup.find('article-id', {'pub-id-type': 'doi'})
            if doi:
                metadata['doi'] = doi.get_text(strip=True)
            
            # PMC ID
            pmc_id = soup.find('article-id', {'pub-id-type': 'pmc'})
            if pmc_id:
                metadata['pmc_id'] = pmc_id.get_text(strip=True)
            
            # Keywords
            keywords = soup.find_all('kwd')
            if keywords:
                metadata['keywords'] = [kwd.get_text(strip=True) for kwd in keywords]
        
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")
        
        return metadata
    
    def _extract_authors(self, soup: BeautifulSoup) -> List[str]:
        """Extract author names."""
        authors = []
        
        contrib_group = soup.find('contrib-group')
        if contrib_group:
            contribs = contrib_group.find_all('contrib', {'contrib-type': 'author'})
            
            for contrib in contribs:
                name_parts = []
                
                surname = contrib.find('surname')
                if surname:
                    name_parts.append(surname.get_text(strip=True))
                
                given_names = contrib.find('given-names')
                if given_names:
                    name_parts.insert(0, given_names.get_text(strip=True))
                
                if name_parts:
                    authors.append(' '.join(name_parts))
        
        return authors
