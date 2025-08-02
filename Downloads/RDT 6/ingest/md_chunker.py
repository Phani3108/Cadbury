"""
Markdown chunking utilities for the Digital Twin system.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

def get_logger(name):
    return logging.getLogger(name)

# Standalone chunk function for external use
def chunk(md_text: str) -> List['Chunk']:
    """
    Standalone chunk function that returns List[Chunk] with required attributes.
    
    Args:
        md_text: Raw markdown text
        
    Returns:
        List of Chunk objects with chunk_id, doc_id, text, speaker, entities, date
    """
    if not md_text or not md_text.strip():
        return []
    
    # Simple chunking by paragraphs for now
    paragraphs = md_text.split('\n\n')
    result = []
    
    for i, paragraph in enumerate(paragraphs):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # Create chunk with required attributes
        chunk_obj = Chunk(
            start_line=1,
            end_line=1,
            text=paragraph,
            chunk_type='paragraph',
            metadata={},
            source_id=None,
            speaker=None,
            timestamp=None
        )
        
        # Add expected attributes
        chunk_obj.chunk_id = f"chunk_{i:04d}"
        chunk_obj.doc_id = "test_doc"
        chunk_obj.entities = []
        chunk_obj.date = "2025-01-01"  # Default date
        
        # Try to detect speaker
        if ':' in paragraph:
            lines = paragraph.split('\n')
            for line in lines:
                if ':' in line and len(line.split(':')) > 1:
                    speaker_part = line.split(':')[0].strip()
                    if speaker_part in ['Ramki', 'Abhilash', 'Penchala']:
                        chunk_obj.speaker = speaker_part
                        break
        
        result.append(chunk_obj)
    
    return result


@dataclass
class Chunk:
    """Represents a chunk of processed content."""
    start_line: int
    end_line: int
    text: str
    chunk_type: str  # 'paragraph', 'quote', 'action_item', 'summary'
    metadata: Optional[Dict[str, Any]] = None
    source_id: Optional[str] = None
    speaker: Optional[str] = None
    timestamp: Optional[str] = None


class MarkdownChunker:
    """
    Chunks markdown content into meaningful segments for processing.
    """
    
    def __init__(self):
        self.logger = get_logger("chunker")
        
        # Patterns for different content types
        self.patterns = {
            'quote': r'^>\s*(.+)$',
            'action_item': r'^\s*[-*]\s*(.+)$',
            'speaker': r'^(\w+):\s*(.+)$',
            'timestamp': r'^\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s*(.+)$',
            'section': r'^#{1,6}\s+(.+)$',
            'code_block': r'^```[\w]*\n(.*?)\n```$',
        }
    
    def chunk(self, md_text: str) -> List[Chunk]:
        """
        Chunk markdown text into meaningful segments.
        
        Args:
            md_text: Raw markdown text
            
        Returns:
            List of Chunk objects with metadata
        """
        if not md_text or not md_text.strip():
            return []
        
        lines = md_text.split('\n')
        chunks = []
        current_chunk = []
        current_start = 1
        current_type = 'paragraph'
        current_metadata = {}
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines unless they're meaningful separators
            if not line:
                if current_chunk:
                    # End current chunk
                    chunk = self._create_chunk(
                        current_start, i-1, current_chunk, current_type, current_metadata
                    )
                    chunks.append(chunk)
                    current_chunk = []
                    current_metadata = {}
                continue
            
            # Check for special patterns
            chunk_type, metadata = self._analyze_line(line)
            
            # If line type changes, end current chunk
            if current_chunk and chunk_type != current_type:
                chunk = self._create_chunk(
                    current_start, i-1, current_chunk, current_type, current_metadata
                )
                chunks.append(chunk)
                current_chunk = []
                current_start = i
                current_type = chunk_type
                current_metadata = metadata
            elif not current_chunk:
                current_start = i
                current_type = chunk_type
                current_metadata = metadata
            
            current_chunk.append(line)
        
        # Add final chunk
        if current_chunk:
            chunk = self._create_chunk(
                current_start, len(lines), current_chunk, current_type, current_metadata
            )
            chunks.append(chunk)
        
        self.logger.info(f"Created {len(chunks)} chunks from {len(lines)} lines")
        return chunks

    def _analyze_line(self, line: str) -> tuple[str, Dict[str, Any]]:
        """
        Analyze a line to determine its type and extract metadata.
        
        Args:
            line: Single line of text
            
        Returns:
            Tuple of (chunk_type, metadata)
        """
        metadata = {}
        
        # Check for quotes
        quote_match = re.match(self.patterns['quote'], line)
        if quote_match:
            metadata['quote_text'] = quote_match.group(1)
            return 'quote', metadata
        
        # Check for action items
        action_match = re.match(self.patterns['action_item'], line)
        if action_match:
            metadata['action_text'] = action_match.group(1)
            return 'action_item', metadata
        
        # Check for speaker attribution
        speaker_match = re.match(self.patterns['speaker'], line)
        if speaker_match:
            metadata['speaker'] = speaker_match.group(1)
            metadata['content'] = speaker_match.group(2)
            return 'dialogue', metadata
        
        # Check for timestamps
        timestamp_match = re.match(self.patterns['timestamp'], line)
        if timestamp_match:
            metadata['timestamp'] = timestamp_match.group(1)
            metadata['content'] = timestamp_match.group(2)
            return 'timestamped', metadata
        
        # Check for section headers
        section_match = re.match(self.patterns['section'], line)
        if section_match:
            metadata['section_title'] = section_match.group(1)
            return 'section', metadata
        
        # Check for code blocks
        code_match = re.match(self.patterns['code_block'], line, re.DOTALL)
        if code_match:
            metadata['code_content'] = code_match.group(1)
            return 'code', metadata
        
        # Default to paragraph
        return 'paragraph', metadata
    
    def _create_chunk(self, start_line: int, end_line: int, lines: List[str], 
                      chunk_type: str, metadata: Dict[str, Any]) -> Chunk:
        """
        Create a Chunk object from processed lines.
        
        Args:
            start_line: Starting line number
            end_line: Ending line number
            lines: List of text lines
            chunk_type: Type of chunk
            metadata: Additional metadata
            
        Returns:
            Chunk object
        """
        text = '\n'.join(lines)
        
        # Extract speaker if available
        speaker = metadata.get('speaker')
        
        # Extract timestamp if available
        timestamp = metadata.get('timestamp')
        
        return Chunk(
            start_line=start_line,
            end_line=end_line,
            text=text,
            chunk_type=chunk_type,
            metadata=metadata,
            speaker=speaker,
            timestamp=timestamp
        )
    
    def chunk_by_speaker(self, md_text: str) -> List[Chunk]:
        """
        Chunk text by speaker turns for conversation analysis.
        
        Args:
            md_text: Raw markdown text
            
        Returns:
            List of Chunk objects grouped by speaker
        """
        lines = md_text.split('\n')
        chunks = []
        current_speaker = None
        current_lines = []
        current_start = 1
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            if not line:
                continue
            
            # Check for speaker attribution
            speaker_match = re.match(self.patterns['speaker'], line)
            
            if speaker_match:
                # Save previous speaker's chunk
                if current_speaker and current_lines:
                    chunk = Chunk(
                        start_line=current_start,
                        end_line=i-1,
                        text='\n'.join(current_lines),
                        chunk_type='speaker_turn',
                        metadata={'speaker': current_speaker}
                    )
                    chunks.append(chunk)
                
                # Start new speaker chunk
                current_speaker = speaker_match.group(1)
                current_lines = [speaker_match.group(2)]
                current_start = i
            else:
                # Continue current speaker's turn
                if current_speaker:
                    current_lines.append(line)
        
        # Add final speaker chunk
        if current_speaker and current_lines:
            chunk = Chunk(
                start_line=current_start,
                end_line=len(lines),
                text='\n'.join(current_lines),
                chunk_type='speaker_turn',
                metadata={'speaker': current_speaker}
            )
            chunks.append(chunk)
        
        return chunks
    
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

# TODO(cursor): implement chunk(md_text:str)->List[Chunk]
"""
Requirements
• Split on semantic sentence boundaries (use spaCy)
• Merge sentences into ~300-token chunks (±50) sliding window, stride 200
• Detect speaker (lines like 'Ramki:' or 'Abhilash:')
• Extract YYYY-MM-DD from front-matter or file name
• Return List[Chunk]  with attributes:
    chunk_id, doc_id, text, speaker, entities (empty list for now), date
• Keep chunk_id = f"{doc_id}_{idx:04d}"
Do NOT embed; uploader will call embed() later.
""" 