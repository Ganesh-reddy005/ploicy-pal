#!/usr/bin/env python3
"""
Script to reset Qdrant collection with proper indexes.
Run this if you see "Index required but not found for document_id" error.
"""

import sys
from app.config import settings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

def reset_collection():
    """Delete and recreate Qdrant collection with proper indexes."""
    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key
    )
    
    collection_name = settings.qdrant_collection
    
    print(f"Checking collection: {collection_name}")
    
    # Check if collection exists
    collections = client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)
    
    if exists:
        response = input(f"Collection '{collection_name}' exists. Delete and recreate? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return
        
        print(f"Deleting collection: {collection_name}")
        client.delete_collection(collection_name=collection_name)
        print("✓ Collection deleted")
    
    # Create collection
    print(f"Creating collection: {collection_name}")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=settings.vector_size,
            distance=Distance.COSINE
        )
    )
    print("✓ Collection created")
    
    # Create payload index for document_id
    print("Creating payload index for document_id...")
    client.create_payload_index(
        collection_name=collection_name,
        field_name="document_id",
        field_schema=PayloadSchemaType.KEYWORD
    )
    print("✓ Payload index created")
    
    print("\n✅ Collection setup complete!")
    print(f"Collection: {collection_name}")
    print(f"Vector size: {settings.vector_size}")
    print(f"Distance: COSINE")
    print(f"Indexes: document_id (KEYWORD)")

if __name__ == "__main__":
    try:
        reset_collection()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
