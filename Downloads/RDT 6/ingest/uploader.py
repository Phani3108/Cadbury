"""
Usage:
    python -m ingest.uploader /path/to/json_dir
"""
import os, json, glob
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from ingest.md_chunker import chunk
from ingest.quote_rewriter import rewrite_quote
from ingest.embed import get_embedding, batch_get_embeddings
from dotenv import load_dotenv
load_dotenv()

def get_azure_search_client():
    """Get Azure Search client."""
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    key = os.getenv("AZURE_SEARCH_KEY")
    index_name = os.getenv("AZURE_INDEX", "dt-chunks-v2")  # Use new index name
    
    if not all([endpoint, key]):
        raise ValueError("Azure Search environment variables not configured")
    
    credential = AzureKeyCredential(key)
    return SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

def process_file(path: str):
    """Process a single JSON file and yield documents for upload."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Extract metadata
    doc_id = os.path.basename(path).replace('.json', '')
    date = data.get('date', '')
    attendees = data.get('attendees', [])
    content = data.get('content', '')
    
    # Chunk the content with new speaker-turn logic
    chunks = chunk(content, doc_id)
    
    # Batch process embeddings for efficiency
    texts = []
    for c in chunks:
        # Process Ramki quotes
        if c.speaker == "Ramki":
            c.text = rewrite_quote(c.text)
        texts.append(c.text)
    
    # Get embeddings in batch
    embeddings = batch_get_embeddings(texts)
    
    for i, (c, embedding) in enumerate(zip(chunks, embeddings)):
        doc = {
            "id": c.chunk_id,  # Use chunk_id from new chunker
            "doc_id": c.doc_id,
            "text": c.text,
            "date": c.date or date,
            "meeting_date": c.meeting_date,
            "attendees": attendees,
            "entities": c.entities or [],
            "speaker": c.speaker,
            "topic_tags": c.topic_tags or [],
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

def main(directory: str, dry_run: bool = False, rechunk: bool = False):
    """Main function to upload documents."""
    try:
        if dry_run:
            print(f"🔍 DRY RUN MODE - Would upload documents from {directory}")
            # Count documents that would be uploaded
            total_chunks = 0
            for json_file in glob.glob(os.path.join(directory, "*.json")):
                chunks = list(process_file(json_file))
                total_chunks += len(chunks)
                print(f"  {os.path.basename(json_file)}: {len(chunks)} chunks")
            print(f"📊 Total chunks: {total_chunks}")
            return
        
        if rechunk:
            print("🔄 Rechunking mode - processing with new speaker-turn logic")
        
        upload_documents(directory)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload documents to Azure Search")
    parser.add_argument("directory", help="Directory containing JSON files")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded")
    parser.add_argument("--rechunk", action="store_true", help="Use new speaker-turn chunking")
    
    args = parser.parse_args()
    
    main(args.directory, dry_run=args.dry_run, rechunk=args.rechunk) 