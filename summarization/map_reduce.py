"""
Map-reduce summarization orchestrator.
"""
import re
from typing import Dict, List, Optional
import logging

from processing.section_parser import Section
from processing.chunker import TextChunker, Chunk
from summarization.llm_client import LLMClient
from summarization import prompts

logger = logging.getLogger(__name__)


class MapReduceSummarizer:
    """Orchestrate map-reduce summarization of document sections."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        chunker: TextChunker
    ):
        """
        Initialize summarizer.
        
        Args:
            llm_client: LLM client for API calls
            chunker: Text chunker
        """
        self.llm = llm_client
        self.chunker = chunker
    
    def summarize_section(
        self,
        section: Section,
        max_chunks: int = 20
    ) -> str:
        """
        Summarize a section using map-reduce.
        
        Args:
            section: Section to summarize
            max_chunks: Maximum chunks to process
            
        Returns:
            Section summary
        """
        logger.info(f"Summarizing section: {section.name}")
        
        # Check if section is short enough to summarize directly
        token_count = self.chunker.count_tokens(section.content)
        
        if token_count <= self.llm.max_tokens * 0.7:  # Leave room for prompt
            logger.info(f"Section {section.name} is short, summarizing directly")
            return self._summarize_directly(section)
        
        # Chunk section
        chunks = self.chunker.chunk(section.content, section.name)
        
        if len(chunks) > max_chunks:
            logger.warning(
                f"Section {section.name} has {len(chunks)} chunks, "
                f"truncating to {max_chunks}"
            )
            chunks = chunks[:max_chunks]
        
        # Map phase: Summarize each chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks):
            logger.debug(f"Summarizing chunk {i+1}/{len(chunks)} of {section.name}")
            summary = self._summarize_chunk(section.name, chunk)
            chunk_summaries.append(summary)
        
        # Reduce phase: Combine chunk summaries
        if len(chunk_summaries) == 1:
            return chunk_summaries[0]
        
        logger.info(f"Combining {len(chunk_summaries)} chunk summaries for {section.name}")
        return self._combine_summaries(section.name, chunk_summaries)
    
    def _summarize_directly(self, section: Section) -> str:
        """Summarize short section directly without chunking."""
        prompt = prompts.get_chunk_summary_prompt(section.name, section.content)
        
        response = self.llm.complete(
            prompt=prompt,
            system_prompt=prompts.PromptTemplates.SYSTEM_PROMPT,
            temperature=0.2
        )
        
        return response.strip()
    
    def _summarize_chunk(self, section_name: str, chunk: Chunk) -> str:
        """Summarize a single chunk (map phase)."""
        prompt = prompts.get_chunk_summary_prompt(section_name, chunk.text)
        
        response = self.llm.complete(
            prompt=prompt,
            system_prompt=prompts.PromptTemplates.SYSTEM_PROMPT,
            temperature=0.2
        )
        
        return response.strip()
    
    def _combine_summaries(
        self,
        section_name: str,
        summaries: List[str]
    ) -> str:
        """Combine chunk summaries into section summary (reduce phase)."""
        # Format summaries
        formatted_summaries = "\n\n".join(
            f"CHUNK {i+1}:\n{summary}"
            for i, summary in enumerate(summaries)
        )
        
        prompt = prompts.get_section_synthesis_prompt(
            section_name=section_name,
            chunk_summaries=formatted_summaries,
            num_chunks=len(summaries)
        )
        
        response = self.llm.complete(
            prompt=prompt,
            system_prompt=prompts.PromptTemplates.SYSTEM_PROMPT,
            temperature=0.2
        )
        
        return response.strip()
    
    def summarize_all_sections(
        self,
        sections: Dict[str, Section]
    ) -> Dict[str, str]:
        """
        Summarize all sections.
        
        Args:
            sections: Dictionary of sections
            
        Returns:
            Dictionary mapping section names to summaries
        """
        summaries = {}
        
        for name, section in sections.items():
            try:
                summary = self.summarize_section(section)
                summaries[name] = summary
            except Exception as e:
                logger.error(f"Error summarizing section {name}: {e}")
                # Continue with other sections
                summaries[name] = f"[Error summarizing section: {str(e)[:100]}]"
        
        return summaries
    
    def extract_structured_info(
        self,
        sections: Dict[str, Section],
        section_summaries: Dict[str, str],
        preamble: str = ""
    ) -> dict:
        """
        Extract structured information for final summary.
        
        Args:
            sections: Original sections
            section_summaries: Section summaries
            preamble: Text before first section (often contains abstract)
            
        Returns:
            Dictionary with structured information
        """
        result = {}
        
        # Extract metadata (objective, study type, population)
        metadata_text = self._get_metadata_text(sections, preamble)
        if metadata_text:
            try:
                metadata = self._extract_metadata(metadata_text)
                result.update(metadata)
            except Exception as e:
                logger.error(f"Error extracting metadata: {e}")
        
        # Extract methods summary (use raw section content when available for better detail)
        methods_source = ""
        if 'methods' in sections:
            methods_source = self.chunker.truncate_to_tokens(
                sections['methods'].content, 2000
            )
        elif 'methods' in section_summaries:
            methods_source = section_summaries['methods']
        if methods_source:
            try:
                result['methods'] = self._extract_methods(methods_source)
            except Exception as e:
                logger.error(f"Error extracting methods: {e}")
                result['methods'] = section_summaries.get('methods', '')
        
        # Extract key findings
        if 'results' in section_summaries:
            try:
                findings = self._extract_findings(section_summaries['results'])
                result['key_findings'] = findings
            except Exception as e:
                logger.error(f"Error extracting findings: {e}")
                result['key_findings'] = [section_summaries['results']]
        
        # Extract limitations
        limitations_text = self._get_limitations_text(sections, section_summaries)
        if limitations_text:
            try:
                limitations = self._extract_limitations(limitations_text)
                result['limitations'] = limitations
            except Exception as e:
                logger.error(f"Error extracting limitations: {e}")
                result['limitations'] = []
        
        # Extract conclusions
        conclusion_text = self._get_conclusion_text(sections, section_summaries)
        if conclusion_text:
            try:
                conclusions = self._extract_conclusions(conclusion_text)
                result['author_conclusions'] = conclusions
            except Exception as e:
                logger.error(f"Error extracting conclusions: {e}")
                result['author_conclusions'] = ""
        
        return result
    
    def _get_metadata_text(self, sections: Dict[str, Section], preamble: str = "") -> str:
        """Get text for metadata extraction (objective, study_type, population)."""
        parts = []
        if 'abstract' in sections:
            parts.append(sections['abstract'].content)
        elif preamble:
            parts.append(preamble)
        if 'introduction' in sections:
            intro = self.chunker.truncate_to_tokens(
                sections['introduction'].content, 1200
            )
            parts.append(intro)
        # Include methods start - study_type and population often appear there
        if 'methods' in sections:
            methods = self.chunker.truncate_to_tokens(
                sections['methods'].content, 800
            )
            parts.append(f"METHODS:\n{methods}")
        return "\n\n".join(parts) if parts else ""
    
    def _get_limitations_text(
        self,
        sections: Dict[str, Section],
        summaries: Dict[str, str]
    ) -> str:
        """Get text for limitations extraction."""
        if 'limitations' in sections:
            return sections['limitations'].content
        elif 'discussion' in summaries:
            return summaries['discussion']
        return ""
    
    def _get_conclusion_text(
        self,
        sections: Dict[str, Section],
        summaries: Dict[str, str]
    ) -> str:
        """Get text for conclusions extraction."""
        if 'conclusion' in summaries:
            return summaries['conclusion']
        elif 'discussion' in summaries:
            return summaries['discussion']
        return ""
    
    def _extract_metadata(self, text: str) -> dict:
        """Extract study metadata."""
        prompt = prompts.get_metadata_prompt(text)
        
        response = self.llm.complete(
            prompt=prompt,
            system_prompt=prompts.PromptTemplates.SYSTEM_PROMPT,
            temperature=0.1,
            json_mode=True
        )
        
        return self.llm.parse_json_response(response)
    
    def _extract_methods(self, methods_text: str) -> str:
        """Extract methods summary."""
        prompt = prompts.get_methods_prompt(methods_text)
        
        response = self.llm.complete(
            prompt=prompt,
            system_prompt=prompts.PromptTemplates.SYSTEM_PROMPT,
            temperature=0.2
        )
        
        text = response.strip()
        # Remove leading markdown headers (## or ###) if LLM added them
        text = re.sub(r'^#+\s*[^\n]+\n*', '', text).strip()
        return text
    
    def _extract_findings(self, results_text: str) -> List[str]:
        """Extract key findings as list."""
        prompt = prompts.get_findings_prompt(results_text)
        
        response = self.llm.complete(
            prompt=prompt,
            system_prompt=prompts.PromptTemplates.SYSTEM_PROMPT,
            temperature=0.1,
            json_mode=True
        )
        
        findings = self.llm.parse_json_response(response)
        
        if isinstance(findings, list):
            return findings
        else:
            return [str(findings)]
    
    def _extract_limitations(self, text: str) -> List[str]:
        """Extract limitations as list."""
        prompt = prompts.get_limitations_prompt(text)
        
        response = self.llm.complete(
            prompt=prompt,
            system_prompt=prompts.PromptTemplates.SYSTEM_PROMPT,
            temperature=0.1,
            json_mode=True
        )
        
        limitations = self.llm.parse_json_response(response)
        
        if isinstance(limitations, list):
            return limitations
        else:
            return []
    
    def _extract_conclusions(self, text: str) -> str:
        """Extract author conclusions."""
        prompt = prompts.get_conclusions_prompt(text)
        
        response = self.llm.complete(
            prompt=prompt,
            system_prompt=prompts.PromptTemplates.SYSTEM_PROMPT,
            temperature=0.2
        )
        
        return response.strip()
