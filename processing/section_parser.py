"""
Section detection and parsing for research papers.
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Section:
    """Represents a paper section."""
    name: str
    content: str
    start_index: int
    end_index: int
    
    def __len__(self) -> int:
        """Return content length."""
        return len(self.content)


class SectionParser:
    """Parse research papers into structured sections."""
    
    # Standard section headers (in typical order)
    SECTION_HEADERS = [
        'abstract',
        'introduction',
        'background',
        'methods',
        'methodology',
        'materials and methods',
        'patients and methods',
        'results',
        'findings',
        'discussion',
        'limitations',
        'conclusion',
        'conclusions',
        'acknowledgments',
        'acknowledgements',
        'references',
    ]
    
    # Section header patterns
    # Each pattern can be preceded by optional numbering (e.g., "1. ", "2. ")
    # to handle common journal formats like "1. Introduction", "2. Materials and Methods"
    _NUM_PREFIX = r'(?:\d+\.\s*)?'
    HEADER_PATTERNS = {
        'abstract': [
            r'\bABSTRACT\b',
            r'\bSummary\b',
        ],
        'introduction': [
            r'\bINTRODUCTION\b',
            r'\bBackground\b',
        ],
        'methods': [
            r'\bMETHODS?\b',
            r'\bMETHODOLOGY\b',
            r'\bMATERIALS?\s+AND\s+METHODS?\b',
            r'\bPATIENTS?\s+AND\s+METHODS?\b',
            r'\bSTUDY\s+DESIGN\b',
        ],
        'results': [
            r'\bRESULTS?\b',
            r'\bFINDINGS?\b',
        ],
        'discussion': [
            r'\bDISCUSSION\b',
        ],
        'limitations': [
            r'\bLIMITATIONS?\b',
            r'\bSTUDY\s+LIMITATIONS?\b',
        ],
        'conclusion': [
            r'\bCONCLUSIONS?\b',
            r'\bCONCLUDING\s+REMARKS?\b',
        ],
    }
    
    def parse(self, text: str) -> Dict[str, Section]:
        """
        Parse text into sections.
        
        Args:
            text: Full paper text
            
        Returns:
            Dictionary mapping section names to Section objects
        """
        # Find all section boundaries
        boundaries = self._find_section_boundaries(text)
        
        if not boundaries:
            logger.warning("No section headers detected, treating as single section")
            return {
                'full_text': Section(
                    name='full_text',
                    content=text,
                    start_index=0,
                    end_index=len(text)
                )
            }
        
        # Detect implicit abstract: substantial text before first section (e.g. before "1. Introduction")
        first_boundary_pos = boundaries[0][1]
        first_boundary_name = boundaries[0][0]
        implicit_abstract = (
            first_boundary_name != 'abstract'
            and first_boundary_pos > 200
            and self._looks_like_abstract(text[:first_boundary_pos])
        )
        if implicit_abstract:
            boundaries.insert(0, ('abstract', 0))
            # Re-sort since we inserted at 0 (first boundary pos is 0, others unchanged)
            boundaries.sort(key=lambda x: x[1])
        
        # Extract sections
        sections = {}
        for i, (section_name, start_pos) in enumerate(boundaries):
            # Determine end position
            if i + 1 < len(boundaries):
                end_pos = boundaries[i + 1][1]
            else:
                end_pos = len(text)
            
            content = text[start_pos:end_pos].strip()
            
            # Remove section header from content
            content = self._remove_header(content, section_name)
            
            if content:
                sections[section_name] = Section(
                    name=section_name,
                    content=content,
                    start_index=start_pos,
                    end_index=end_pos
                )
        
        return sections
    
    def _looks_like_abstract(self, text: str) -> bool:
        """Heuristic: text before first section likely an unlabeled abstract."""
        if len(text.strip()) < 150:
            return False
        # Skip if it looks like metadata (affiliations, emails, etc.)
        lower = text.lower()
        if '@' in lower and lower.count('@') > 1:
            return False  # Multiple emails = likely correspondence block
        if lower.count('department') > 2 or lower.count('university') > 3:
            return False  # Heavy affiliation block
        # Should contain sentence-like structure (periods, normal words)
        words = text.split()
        if len(words) < 30:
            return False
        return True
    
    def _find_section_boundaries(self, text: str) -> List[Tuple[str, int]]:
        """
        Find section boundaries in text.
        
        Returns:
            List of (section_name, start_position) tuples
        """
        boundaries = []
        
        for section_name, patterns in self.HEADER_PATTERNS.items():
            for pattern in patterns:
                # Look for pattern at start of line (with optional numbering: "1. ", "2. ")
                full_pattern = r'^\s*' + self._NUM_PREFIX + pattern + r'\s*$'
                regex = re.compile(full_pattern, re.MULTILINE | re.IGNORECASE)
                
                for match in regex.finditer(text):
                    boundaries.append((section_name, match.start()))
        
        # Sort by position
        boundaries.sort(key=lambda x: x[1])
        
        # Remove duplicates (keep first occurrence of each section)
        seen_sections = set()
        unique_boundaries = []
        for section_name, pos in boundaries:
            if section_name not in seen_sections:
                seen_sections.add(section_name)
                unique_boundaries.append((section_name, pos))
        
        return unique_boundaries
    
    def _remove_header(self, content: str, section_name: str) -> str:
        """Remove section header from content."""
        lines = content.split('\n')
        
        # Check if first line is section header
        if lines and lines[0].strip():
            first_line = lines[0].strip()
            # Strip optional leading numbering (e.g., "1. ", "2. ") for pattern matching
            first_line_normalized = re.sub(r'^\d+\.\s*', '', first_line).upper()
            
            # Check against patterns
            patterns = self.HEADER_PATTERNS.get(section_name, [])
            for pattern in patterns:
                if re.search(pattern, first_line_normalized, re.IGNORECASE):
                    # Remove first line
                    return '\n'.join(lines[1:]).strip()
        
        return content
    
    def get_section_order(self, sections: Dict[str, Section]) -> List[str]:
        """
        Get sections in logical order.
        
        Args:
            sections: Dictionary of sections
            
        Returns:
            Ordered list of section names
        """
        # Create order map
        order_map = {name: i for i, name in enumerate(self.SECTION_HEADERS)}
        
        # Sort sections by standard order, with unknown sections at end
        def sort_key(name: str) -> int:
            return order_map.get(name.lower(), 999)
        
        return sorted(sections.keys(), key=sort_key)
    
    def merge_related_sections(self, sections: Dict[str, Section]) -> Dict[str, Section]:
        """
        Merge related sections (e.g., multiple methods sections).
        
        Args:
            sections: Dictionary of sections
            
        Returns:
            Dictionary with merged sections
        """
        merged = {}
        
        # Group related sections
        methods_content = []
        results_content = []
        discussion_content = []
        
        for name, section in sections.items():
            name_lower = name.lower()
            
            if any(m in name_lower for m in ['method', 'material', 'patient']):
                methods_content.append(section.content)
            elif 'result' in name_lower or 'finding' in name_lower:
                results_content.append(section.content)
            elif 'discussion' in name_lower:
                discussion_content.append(section.content)
            else:
                merged[name] = section
        
        # Create merged sections
        if methods_content:
            merged['methods'] = Section(
                name='methods',
                content='\n\n'.join(methods_content),
                start_index=0,
                end_index=0
            )
        
        if results_content:
            merged['results'] = Section(
                name='results',
                content='\n\n'.join(results_content),
                start_index=0,
                end_index=0
            )
        
        if discussion_content:
            merged['discussion'] = Section(
                name='discussion',
                content='\n\n'.join(discussion_content),
                start_index=0,
                end_index=0
            )
        
        return merged
    
    def validate_sections(self, sections: Dict[str, Section]) -> bool:
        """
        Validate that essential sections are present.
        
        Args:
            sections: Dictionary of sections
            
        Returns:
            True if valid structure detected
        """
        section_names = set(s.lower() for s in sections.keys())
        
        # Check for at least abstract OR (methods AND results)
        has_abstract = 'abstract' in section_names
        has_methods = 'methods' in section_names or 'methodology' in section_names
        has_results = 'results' in section_names or 'findings' in section_names
        
        return has_abstract or (has_methods and has_results)
