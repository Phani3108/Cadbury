"""
Markdown chunking utilities for the Digital Twin system.
"""

import re
import tiktoken
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime

def get_logger(name):
    return logging.getLogger(name)

# Initialize BPE tokenizer for accurate token counting
tokenizer = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """Count tokens using BPE tokenizer."""
    return len(tokenizer.encode(text))

def extract_meeting_date(filename: str) -> str:
    """Extract meeting date from filename like '2025-01-15_Meeting_Title.json'."""
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    return date_match.group(1) if date_match else "2025-01-01"

def extract_speaker_tags(text: str) -> List[str]:
    """Extract topic tags from text content."""
    # Simple topic extraction - can be enhanced later
    topics = []
    if any(word in text.lower() for word in ['optum', 'mississippi', 'sigma']):
        if 'optum' in text.lower():
            topics.append('optum')
        if 'mississippi' in text.lower():
            topics.append('mississippi')
        if 'sigma' in text.lower():
            topics.append('sigma')
    return topics

# Standalone chunk function for external use
def chunk(md_text: str, doc_id: str = "default_doc") -> List['Chunk']:
    """
    Enhanced chunk function with speaker-turn logic.
    
    Args:
        md_text: Raw markdown text
        doc_id: Document identifier
        
    Returns:
        List of Chunk objects with chunk_id, doc_id, text, speaker, entities, date
    """
    if not md_text or not md_text.strip():
        return []
    
    # Extract meeting date from doc_id if it contains date
    meeting_date = extract_meeting_date(doc_id)
    
    # Split on speaker patterns: \n<speaker>:
    speaker_pattern = r'\n([A-Za-z]+):\s*'
    parts = re.split(speaker_pattern, md_text)
    
    chunks = []
    current_chunk_lines = []
    current_speaker = None
    current_tokens = 0
    chunk_idx = 0
    MAX_TOKENS = 200
    
    for i, part in enumerate(parts):
        if i == 0:  # First part is content before any speaker
            if part.strip():
                current_chunk_lines.append(part.strip())
                current_tokens = count_tokens(part.strip())
        elif i % 2 == 1:  # Speaker name
            speaker = part.strip()
            
            # If we have a previous speaker and content, check if we need to start new chunk
            if current_speaker and current_chunk_lines:
                # Check if adding this speaker would exceed token limit
                speaker_content = f"{speaker}: "
                speaker_tokens = count_tokens(speaker_content)
                
                if current_tokens + speaker_tokens > MAX_TOKENS and current_chunk_lines:
                    # Create chunk from current content
                    chunk_text = '\n'.join(current_chunk_lines)
                    topic_tags = extract_speaker_tags(chunk_text)
                    
                    chunk_obj = Chunk(
                        start_line=1,
                        end_line=1,
                        text=chunk_text,
                        chunk_type='speaker_turn',
                        metadata={
                            'speaker': current_speaker,
                            'meeting_date': meeting_date,
                            'topic_tags': topic_tags
                        },
                        source_id=doc_id,
                        speaker=current_speaker,
                        timestamp=None
                    )
                    
                    # Add expected attributes
                    chunk_obj.chunk_id = f"{doc_id}_{chunk_idx:04d}"
                    chunk_obj.doc_id = doc_id
                    chunk_obj.entities = []
                    chunk_obj.date = meeting_date
                    chunk_obj.meeting_date = meeting_date
                    chunk_obj.topic_tags = topic_tags
                    
                    chunks.append(chunk_obj)
                    chunk_idx += 1
                    
                    # Start new chunk
                    current_chunk_lines = [speaker_content]
                    current_tokens = speaker_tokens
                    current_speaker = speaker
                else:
                    # Continue with same speaker
                    current_chunk_lines.append(speaker_content)
                    current_tokens += speaker_tokens
                    current_speaker = speaker
            else:
                # First speaker
                current_chunk_lines.append(f"{speaker}: ")
                current_tokens = count_tokens(f"{speaker}: ")
                current_speaker = speaker
        else:  # Content after speaker
            if part.strip():
                content = part.strip()
                content_tokens = count_tokens(content)
                
                # Check if adding this content would exceed token limit
                if current_tokens + content_tokens > MAX_TOKENS and current_chunk_lines:
                    # Create chunk from current content
                    chunk_text = '\n'.join(current_chunk_lines)
                    topic_tags = extract_speaker_tags(chunk_text)
                    
                    chunk_obj = Chunk(
                        start_line=1,
                        end_line=1,
                        text=chunk_text,
                        chunk_type='speaker_turn',
                        metadata={
                            'speaker': current_speaker,
                            'meeting_date': meeting_date,
                            'topic_tags': topic_tags
                        },
                        source_id=doc_id,
                        speaker=current_speaker,
                        timestamp=None
                    )
                    
                    # Add expected attributes
                    chunk_obj.chunk_id = f"{doc_id}_{chunk_idx:04d}"
                    chunk_obj.doc_id = doc_id
                    chunk_obj.entities = []
                    chunk_obj.date = meeting_date
                    chunk_obj.meeting_date = meeting_date
                    chunk_obj.topic_tags = topic_tags
                    
                    chunks.append(chunk_obj)
                    chunk_idx += 1
                    
                    # Start new chunk with current speaker and content
                    current_chunk_lines = [f"{current_speaker}: {content}"]
                    current_tokens = count_tokens(f"{current_speaker}: {content}")
                else:
                    # Add content to current chunk
                    current_chunk_lines.append(content)
                    current_tokens += content_tokens
    
    # Add final chunk if there's content
    if current_chunk_lines:
        chunk_text = '\n'.join(current_chunk_lines)
        topic_tags = extract_speaker_tags(chunk_text)
        
        chunk_obj = Chunk(
            start_line=1,
            end_line=1,
            text=chunk_text,
            chunk_type='speaker_turn',
            metadata={
                'speaker': current_speaker,
                'meeting_date': meeting_date,
                'topic_tags': topic_tags
            },
            source_id=doc_id,
            speaker=current_speaker,
            timestamp=None
        )
        
        # Add expected attributes
        chunk_obj.chunk_id = f"{doc_id}_{chunk_idx:04d}"
        chunk_obj.doc_id = doc_id
        chunk_obj.entities = []
        chunk_obj.date = meeting_date
        chunk_obj.meeting_date = meeting_date
        chunk_obj.topic_tags = topic_tags
        
        chunks.append(chunk_obj)
    
    return chunks


@dataclass
class Chunk:
    """Represents a chunk of processed content."""
    start_line: int
    end_line: int
    text: str
    chunk_type: str  # 'paragraph', 'quote', 'action_item', 'summary', 'speaker_turn'
    metadata: Optional[Dict[str, Any]] = None
    source_id: Optional[str] = None
    speaker: Optional[str] = None
    timestamp: Optional[str] = None
    
    # Additional fields for enhanced chunking
    chunk_id: Optional[str] = None
    doc_id: Optional[str] = None
    entities: Optional[List[str]] = None
    date: Optional[str] = None
    meeting_date: Optional[str] = None
    topic_tags: Optional[List[str]] = None


class MarkdownChunker:
    """
    Enhanced chunker with speaker-turn logic and token-aware chunking.
    """
    
    def __init__(self):
        self.logger = get_logger("chunker")
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Patterns for different content types
        self.patterns = {
            'quote': r'^>\s*(.+)$',
            'action_item': r'^\s*[-*]\s*(.+)$',
            'speaker': r'^(\w+):\s*(.+)$',
            'timestamp': r'^\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s*(.+)$',
            'section': r'^#{1,6}\s+(.+)$',
            'code_block': r'^```[\w]*\n(.*?)\n```$',
        }
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using BPE tokenizer."""
        return len(self.tokenizer.encode(text))
    
    def chunk(self, md_text: str, doc_id: str = "default_doc") -> List[Chunk]:
        """
        Enhanced chunking with speaker-turn logic and token limits.
        
        Args:
            md_text: Raw markdown text
            doc_id: Document identifier
            
        Returns:
            List of Chunk objects with enhanced metadata
        """
        return chunk(md_text, doc_id)
    
    def chunk_by_speaker(self, md_text: str, doc_id: str = "default_doc") -> List[Chunk]:
        """
        Chunk text by speaker turns with token limits.
        
        Args:
            md_text: Raw markdown text
            doc_id: Document identifier
            
        Returns:
            List of Chunk objects grouped by speaker
        """
        return chunk(md_text, doc_id)
    
    def extract_quotes(self, md_text: str) -> List[Chunk]:
        """
        Extract only quote chunks from markdown text.
        
        Args:
            md_text: Raw markdown text
            
        Returns:
            List of quote Chunk objects
        """
        chunks = self.chunk(md_text)
        return [chunk for chunk in chunks if chunk.chunk_type == 'quote']
    
    def extract_action_items(self, md_text: str) -> List[Chunk]:
        """
        Extract only action item chunks from markdown text.
        
        Args:
            md_text: Raw markdown text
            
        Returns:
            List of action item Chunk objects
        """
        chunks = self.chunk(md_text)
        return [chunk for chunk in chunks if chunk.chunk_type == 'action_item']


# Global chunker instance
chunker = MarkdownChunker() 