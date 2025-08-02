"""
Usage:
    python -m ingest.uploader /path/to/json_dir
"""
import os, json, glob
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from ingest.md_chunker import chunk
from ingest.quote_rewriter import rewrite_quote
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
load_dotenv()

def get_azure_search_client():
    """Get Azure Search client."""
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    key = os.getenv("AZURE_SEARCH_KEY")
    index_name = os.getenv("AZURE_INDEX")
    
    if not all([endpoint, key, index_name]):
        raise ValueError("Azure Search environment variables not configured")
    
    credential = AzureKeyCredential(key)
    return SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

def embed(text: str) -> list:
    """Generate embeddings for text."""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embedding = model.encode(text)
    return embedding.tolist()

def process_file(path: str):
    """Process a single JSON file and yield documents for upload."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Extract metadata
    doc_id = os.path.basename(path).replace('.json', '')
    date = data.get('date', '')
    attendees = data.get('attendees', [])
    content = data.get('content', '')
    
    # Chunk the content
    chunks = chunk(content)
    
    for i, c in enumerate(chunks):
        # Process Ramki quotes
        if c.speaker == "Ramki":
            c.text = rewrite_quote(c.text)
        
        # Generate embedding
        embedding = embed(c.text)
        
        doc = {
            "id": f"{doc_id}_{i:04d}",
            "doc_id": doc_id,
            "text": c.text,
            "date": date,
            "attendees": attendees,
            "entities": c.entities or [],
            "speaker": c.speaker,
            "source_id": f"Source-{doc_id}-{i:04d}",
            "embedding": embedding
        }
        yield doc

def upload_documents(directory: str, batch_size: int = 100):
    """Upload documents to Azure Search."""
    client = get_azure_search_client()
    
    batch = []
    total_uploaded = 0
    
    for json_file in glob.glob(os.path.join(directory, "*.json")):
        print(f"Processing {json_file}...")
        
        for doc in process_file(json_file):
            batch.append(doc)
            
            if len(batch) >= batch_size:
                client.upload_documents(batch)
                total_uploaded += len(batch)
                print(f"Uploaded batch of {len(batch)} documents (total: {total_uploaded})")
                batch.clear()
    
    # Upload remaining documents
    if batch:
        client.upload_documents(batch)
        total_uploaded += len(batch)
        print(f"Uploaded final batch of {len(batch)} documents (total: {total_uploaded})")
    
    print(f"✅ Upload complete: {total_uploaded} documents uploaded to Azure Search")

def main(directory: str, dry_run: bool = False):
    """Main function to upload documents."""
    try:
        if dry_run:
            print(f"🔍 DRY RUN MODE - Would upload documents from {directory}")
            # Count documents that would be uploaded
            import glob
            import json
            json_files = glob.glob(os.path.join(directory, "*.json"))
            total_chunks = 0
            
            for json_file in json_files:
                print(f"📄 Would process: {json_file}")
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        if 'chunks' in data:
                            total_chunks += len(data['chunks'])
                        else:
                            total_chunks += 1  # Assume at least one chunk per file
                except Exception as e:
                    print(f"⚠️ Error reading {json_file}: {e}")
                    total_chunks += 1  # Assume one chunk even if we can't read it
            
            print(f"✅ DRY RUN: Would upload {len(json_files)} files with {total_chunks} total chunks")
            return 0
        else:
            upload_documents(directory)
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return 1
    return 0

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m ingest.uploader <json_directory> [--dry-run]")
        sys.exit(1)
    
    directory = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    
    exit(main(directory, dry_run)) 