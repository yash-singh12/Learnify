import os
import argparse
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from sentence_transformers import SentenceTransformer
import numpy as np

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "learning_path_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "courses")
MODEL_NAME = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")

def connect_mongo():
    return MongoClient(MONGODB_URI)

def compute_embeddings(force=False, batch_size=32):
    print(f"Connecting to MongoDB: {DB_NAME}.{COLLECTION_NAME}")
    client = connect_mongo()
    db = client[DB_NAME]
    col = db[COLLECTION_NAME]

    # Find documents that need embeddings
    if force:
        query = {}
    else:
        query = {"$or": [{"embedding": {"$exists": False}}, {"embedding": None}]}
    
    docs = list(col.find(query))
    total_docs = len(docs)
    
    if total_docs == 0:
        print("No documents found needing embeddings.")
        client.close()
        return

    print(f"Found {total_docs} documents to process. Loading model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    # Prepare text for embedding
    texts = []
    ids = []
    for doc in docs:
        # Concatenate title, description, and tags
        text_parts = [
            doc.get("title", ""),
            doc.get("description", ""),
            " ".join(doc.get("tags", [])) if isinstance(doc.get("tags"), list) else str(doc.get("tags", ""))
        ]
        text = ". ".join([p for p in text_parts if p]).strip()
        texts.append(text)
        ids.append(doc["_id"])

    # Compute embeddings in batches
    print(f"Computing embeddings for {len(texts)} documents...")
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True, convert_to_numpy=True)

    # Update MongoDB
    print("Updating MongoDB...")
    ops = []
    for doc_id, emb in zip(ids, embeddings):
        # Convert numpy array to list of floats
        emb_list = emb.tolist()
        ops.append(UpdateOne({"_id": doc_id}, {"$set": {"embedding": emb_list}}))

    if ops:
        result = col.bulk_write(ops)
        print(f"Updated {result.modified_count} documents.")

    client.close()
    print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Recompute all embeddings")
    args = parser.parse_args()
    
    compute_embeddings(force=args.force)
