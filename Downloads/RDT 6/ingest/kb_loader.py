"""
Knowledge Base Loader for Digital Twin System
Processes JSON files from processed_kb/ and loads them into the system.
Compliant with Truth Policy requirements.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ingest.md_chunker import chunk
from ingest.types import Chunk

class KnowledgeBaseLoader:
    """Loads and processes knowledge base files."""
    
    def __init__(self):
        self.kb_dir = Path("processed_kb")
        self.chunks = []
        self.source_mapping = {}
        
    def load_all_files(self) -> List[Chunk]:
        """Load all JSON files from processed_kb directory."""
        if not self.kb_dir.exists():
            print(f"❌ Knowledge base directory not found: {self.kb_dir}")
            return []
        
        json_files = list(self.kb_dir.glob("*.json"))
        print(f"📚 Found {len(json_files)} JSON files to process")
        
        all_chunks = []
        for file_path in json_files:
            chunks = self.process_file(file_path)
            all_chunks.extend(chunks)
            print(f"  ✅ Processed {file_path.name}: {len(chunks)} chunks")
        
        # Store chunks for later use
        self.chunks = all_chunks
        
        print(f"📊 Total chunks loaded: {len(all_chunks)}")
        return all_chunks
    
    def process_file(self, file_path: Path) -> List[Chunk]:
        """Process a single JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract metadata
            doc_id = file_path.stem
            date = data.get('date', '')
            attendees = data.get('attendees', [])
            content = data.get('content', '')
            
            # Validate age (Truth Policy: 270-day limit)
            if not self._is_recent(date):
                print(f"  ⚠️  Skipping old file: {file_path.name} (date: {date})")
                return []
            
            # Chunk the content
            chunk_list = chunk(content)
            
            # Add metadata to chunks
            processed_chunks = []
            for i, chunk_obj in enumerate(chunk_list):
                # Add source information for Truth Policy compliance
                chunk_obj.source_id = f"Source-{doc_id}-{i:04d}"
                chunk_obj.date = date
                chunk_obj.attendees = attendees
                chunk_obj.doc_id = doc_id
                
                # Add to source mapping for verification
                self.source_mapping[chunk_obj.source_id] = {
                    'doc_id': doc_id,
                    'date': date,
                    'text': chunk_obj.text[:200] + "..." if len(chunk_obj.text) > 200 else chunk_obj.text
                }
                
                processed_chunks.append(chunk_obj)
            
            return processed_chunks
            
        except Exception as e:
            print(f"  ❌ Error processing {file_path.name}: {e}")
            return []
    
    def _is_recent(self, date_str: str) -> bool:
        """Check if date is within 270 days (Truth Policy requirement)."""
        try:
            if not date_str:
                return False
            
            # Parse date (assuming YYYY-MM-DD format)
            file_date = datetime.strptime(date_str, '%Y-%m-%d')
            current_date = datetime.now()
            
            # Check if within 270 days
            age_days = (current_date - file_date).days
            return age_days <= 270
            
        except Exception:
            return False
    
    def get_source_info(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get source information for Truth Policy verification."""
        return self.source_mapping.get(source_id)
    
    def get_recent_chunks(self, days: int = 270) -> List[Chunk]:
        """Get chunks from recent documents only."""
        recent_chunks = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Use the loaded chunks from load_all_files
        for chunk in self.chunks:
            try:
                chunk_date = datetime.strptime(chunk.date, '%Y-%m-%d')
                if chunk_date >= cutoff_date:
                    recent_chunks.append(chunk)
            except Exception:
                continue
        
        return recent_chunks

# Global loader instance
kb_loader = KnowledgeBaseLoader()

def load_knowledge_base() -> List[Chunk]:
    """Load the knowledge base and return chunks."""
    return kb_loader.load_all_files()

def get_source_info(source_id: str) -> Optional[Dict[str, Any]]:
    """Get source information for verification."""
    return kb_loader.get_source_info(source_id)

def get_recent_chunks(days: int = 270) -> List[Chunk]:
    """Get recent chunks for Truth Policy compliance."""
    return kb_loader.get_recent_chunks(days) 