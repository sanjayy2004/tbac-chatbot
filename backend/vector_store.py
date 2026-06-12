import json
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# ── Paths ──────────────────────────────────────────────────────
CHUNKS_PATH = Path("data/processed_chunks.json")
VECTOR_DB_PATH = Path("vector_db/chroma_db")

# ── Load embedding model ───────────────────────────────────────
import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
print("⏳ Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("✅ Embedding model loaded!")

# ── Initialize ChromaDB ────────────────────────────────────────
def get_chroma_client():
    VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
    return client

# ── Create or get collection ───────────────────────────────────
def get_collection(client):
    collection = client.get_or_create_collection(
        name="company_docs",
        metadata={"hnsw:space": "cosine"}
    )
    return collection

# ── Generate embeddings and index ─────────────────────────────
def build_vector_store():
    # Load chunks
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"📄 Loaded {len(chunks)} chunks")

    # Initialize ChromaDB
    client = get_chroma_client()
    collection = get_collection(client)

    # Check if already indexed
    existing = collection.count()
    if existing > 0:
        print(f"⚠️  Collection already has {existing} documents. Clearing and re-indexing...")
        client.delete_collection("company_docs")
        collection = get_collection(client)

    # Process in batches
    batch_size = 10
    total = len(chunks)

    for i in range(0, total, batch_size):
        batch = chunks[i:i+batch_size]

        ids = [chunk["chunk_id"] for chunk in batch]
        texts = [chunk["text"] for chunk in batch]
        metadatas = [
            {
                "source": chunk["source"],
                "department": chunk["department"],
                "file_type": chunk["file_type"],
                "accessible_roles": ",".join(chunk["accessible_roles"])
            }
            for chunk in batch
        ]

        # Generate embeddings
        embeddings = model.encode(texts).tolist()

        # Add to ChromaDB
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        print(f"✅ Indexed batch {i//batch_size + 1}/{(total+batch_size-1)//batch_size} "
              f"({min(i+batch_size, total)}/{total} chunks)")

    print(f"\n🎉 Vector store built! Total indexed: {collection.count()} documents")
    return collection

# ── Semantic search function ───────────────────────────────────
def search(query, user_role, top_k=5):
    client = get_chroma_client()
    collection = get_collection(client)

    # Generate query embedding
    query_embedding = model.encode([query]).tolist()

    # Get all results first, then filter by role
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(top_k * 5, collection.count())
    )

    if not results["documents"][0]:
        return []

    # Filter by role manually
    output = []
    for i, doc in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i]
        accessible_roles = metadata["accessible_roles"].split(",")
        if user_role in accessible_roles:
            output.append({
                "text": doc,
                "source": metadata["source"],
                "department": metadata["department"],
                "distance": results["distances"][0][i]
            })
        if len(output) >= top_k:
            break

    return output

# ── Test search ────────────────────────────────────────────────
def test_search():
    print("\n🔍 Testing search...")
    
    test_cases = [
        ("What is the financial summary?", "finance"),
        ("Tell me about employee policies", "employee"),
        ("What are the marketing campaigns?", "marketing"),
    ]

    for query, role in test_cases:
        print(f"\n Query: '{query}' | Role: {role}")
        results = search(query, role, top_k=2)
        if results:
            for r in results:
                print(f"  📄 Source: {r['source']} | Dept: {r['department']} | Score: {r['distance']:.4f}")
                print(f"  📝 Preview: {r['text'][:100]}...")
        else:
            print("  ❌ No results found")

if __name__ == "__main__":
    build_vector_store()
    test_search()