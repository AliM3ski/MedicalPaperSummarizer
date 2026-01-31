"""
Text chunking with overlap for LLM processing.
"""
import tiktoken
import re
from typing import List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    """Represents a text chunk."""
    text: str
    start_char: int
    end_char: int
    token_count: int
    chunk_index: int


class TextChunker:
    """Chunk text into overlapping segments for LLM processing."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        encoding_name: str = "cl100k_base"
    ):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
            encoding_name: Tiktoken encoding name
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        try:
            self.encoding = tiktoken.get_encoding(encoding_name)
        except Exception as e:
            logger.warning(f"Error loading encoding {encoding_name}: {e}, using cl100k_base")
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def chunk(self, text: str, section_name: Optional[str] = None) -> List[Chunk]:
        """
        Chunk text with overlap.
        
        Args:
            text: Text to chunk
            section_name: Optional section name for logging
            
        Returns:
            List of Chunk objects
        """
        if not text.strip():
            return []
        
        # Split into sentences first
        sentences = self._split_into_sentences(text)
        
        if not sentences:
            return []
        
        # Create chunks
        chunks = []
        current_tokens = []
        current_text = []
        current_start = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_tokens = self.encoding.encode(sentence)
            
            # Check if adding this sentence would exceed chunk size
            if current_tokens and len(current_tokens) + len(sentence_tokens) > self.chunk_size:
                # Create chunk from current content
                chunk_text = ' '.join(current_text)
                chunks.append(Chunk(
                    text=chunk_text,
                    start_char=current_start,
                    end_char=current_start + len(chunk_text),
                    token_count=len(current_tokens),
                    chunk_index=chunk_index
                ))
                
                chunk_index += 1
                
                # Calculate overlap
                overlap_tokens = self.chunk_overlap
                overlap_sentences = []
                overlap_token_count = 0
                
                # Take sentences from end for overlap
                for sent in reversed(current_text):
                    sent_tokens = self.encoding.encode(sent)
                    if overlap_token_count + len(sent_tokens) <= overlap_tokens:
                        overlap_sentences.insert(0, sent)
                        overlap_token_count += len(sent_tokens)
                    else:
                        break
                
                # Start new chunk with overlap
                current_text = overlap_sentences
                current_tokens = self.encoding.encode(' '.join(current_text))
                current_start = chunks[-1].end_char - len(' '.join(overlap_sentences))
            
            # Add sentence to current chunk
            current_text.append(sentence)
            current_tokens.extend(sentence_tokens)
        
        # Add final chunk
        if current_text:
            chunk_text = ' '.join(current_text)
            chunks.append(Chunk(
                text=chunk_text,
                start_char=current_start,
                end_char=current_start + len(chunk_text),
                token_count=len(current_tokens),
                chunk_index=chunk_index
            ))
        
        if section_name:
            logger.info(f"Chunked {section_name}: {len(chunks)} chunks")
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Uses regex-based sentence boundary detection.
        More sophisticated than simple split on periods.
        """
        # Replace newlines with spaces (but preserve paragraph breaks)
        text = re.sub(r'\n+', ' ', text)
        
        # Sentence boundary pattern
        # Matches: . ! ? followed by space and capital letter
        # Avoids: abbreviations (Dr., Mr., etc.), decimals (1.5), etc.
        pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        
        sentences = re.split(pattern, text)
        
        # Clean sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Handle sentences that are too long (split on other punctuation)
        final_sentences = []
        for sent in sentences:
            sent_tokens = len(self.encoding.encode(sent))
            
            if sent_tokens > self.chunk_size * 1.5:
                # Split on semicolons and commas for very long sentences
                subsents = re.split(r'[;,]\s+', sent)
                final_sentences.extend(s.strip() for s in subsents if s.strip())
            else:
                final_sentences.append(sent)
        
        return final_sentences
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count
            
        Returns:
            Token count
        """
        return len(self.encoding.encode(text))
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to maximum token count.
        
        Args:
            text: Text to truncate
            max_tokens: Maximum tokens
            
        Returns:
            Truncated text
        """
        tokens = self.encoding.encode(text)
        
        if len(tokens) <= max_tokens:
            return text
        
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)
    
    def get_chunk_summary(self, chunks: List[Chunk]) -> dict:
        """
        Get summary statistics for chunks.
        
        Args:
            chunks: List of chunks
            
        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'total_tokens': 0,
                'avg_tokens_per_chunk': 0,
                'min_tokens': 0,
                'max_tokens': 0
            }
        
        token_counts = [c.token_count for c in chunks]
        
        return {
            'total_chunks': len(chunks),
            'total_tokens': sum(token_counts),
            'avg_tokens_per_chunk': sum(token_counts) / len(token_counts),
            'min_tokens': min(token_counts),
            'max_tokens': max(token_counts)
        }
