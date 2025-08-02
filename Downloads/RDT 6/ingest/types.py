from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass
class Chunk:
    """Represents a chunk of processed content."""
    chunk_id: str
    doc_id: str
    text: str
    speaker: Optional[str] = None
    entities: List[str] = None
    date: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None 