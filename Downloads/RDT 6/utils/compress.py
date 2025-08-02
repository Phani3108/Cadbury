from typing import List
from ingest.types import Chunk

def compress(chunks: List[Chunk], limit_tokens=1500) -> str:
    """
    Iterative CoD:
      1) Concatenate chunks newer→older.
      2) While tokens > limit: ask o4-mini with prompt
         'Compress but keep key entities & dates.'
      3) Return compressed text.
    """
    # TODO(cursor): implement compress() using openai.ChatCompletion with o4-mini
    pass 