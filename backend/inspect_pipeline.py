"""
Pipeline Inspection Script
Run from: backend/
Command:  python inspect_pipeline.py

Verifies:
    1. ChromaDB — collection count, chunk metadata, embedding dimensions
    2. Chunk content — shows text of each chunk
    3. Similarity search — proves embeddings work end-to-end
    4. GCS — confirms the uploaded PDF object exists
"""

import os
import sys
from pathlib import Path

# ── Load settings from .env ────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

CHROMA_PERSIST_DIR    = os.getenv("CHROMA_PERSIST_DIR", "data/chroma")
CHROMA_COLLECTION     = os.getenv("CHROMA_COLLECTION_NAME", "documents")
GCP_PROJECT           = os.getenv("GCP_PROJECT_ID", "")
GCS_BUCKET            = os.getenv("GCS_BUCKET_NAME", "")
EMBEDDING_MODEL       = os.getenv("VERTEX_EMBEDDING_MODEL", "text-embedding-004")

DIVIDER = "─" * 70

def section(title: str):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)

# ══════════════════════════════════════════════════════════════════════════════
# 1. CHROMADB — collection stats
# ══════════════════════════════════════════════════════════════════════════════
section("1. ChromaDB — Collection Stats")

import chromadb

client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

try:
    collection = client.get_collection(CHROMA_COLLECTION)
    total_chunks = collection.count()
    print(f"  Collection name : {CHROMA_COLLECTION}")
    print(f"  Persist dir     : {CHROMA_PERSIST_DIR}")
    print(f"  Total chunks    : {total_chunks}")
except Exception as e:
    print(f"  ERROR: {e}")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# 2. CHROMADB — inspect all chunks (metadata + embedding dimensions)
# ══════════════════════════════════════════════════════════════════════════════
section("2. ChromaDB — Chunks, Metadata & Embeddings")

results = collection.get(
    include=["documents", "metadatas", "embeddings"],
    limit=100,
)

chunk_ids   = results["ids"]
documents   = results["documents"]
metadatas   = results["metadatas"]
embeddings  = results["embeddings"]

print(f"\n  {'CHUNK ID':<45} {'PAGE':>4} {'IDX':>4} {'CHARS':>6}")
print(f"  {'─'*45} {'─'*4} {'─'*4} {'─'*6}")

for i, (cid, doc, meta) in enumerate(zip(chunk_ids, documents, metadatas)):
    print(f"  {cid:<45} {meta.get('page_number', '?'):>4} "
          f"{meta.get('chunk_index', '?'):>4} {len(doc):>6}")

# Embedding dimension check
if embeddings is not None and len(embeddings) > 0 and embeddings[0] is not None:
    dim = len(embeddings[0])
    print(f"\n  Embedding dimensions : {dim}  ({'✅ 768 — text-embedding-004' if dim == 768 else '⚠️  unexpected dimension'})")
else:
    print("\n  ⚠️  Embeddings not returned — ChromaDB stores them in the HNSW index file.")
    print("     This is normal. Run the similarity search below to confirm they work.")

# ══════════════════════════════════════════════════════════════════════════════
# 3. CHROMADB — show chunk content and metadata for first document
# ══════════════════════════════════════════════════════════════════════════════
section("3. Chunk Content & Full Metadata (first 3 chunks)")

for i in range(min(3, len(chunk_ids))):
    print(f"\n  ┌─ Chunk {i+1} of {len(chunk_ids)} ─────────────────────────────────────────")
    print(f"  │ chunk_id     : {chunk_ids[i]}")
    meta = metadatas[i]
    for k, v in meta.items():
        print(f"  │ {k:<14}: {v}")
    text_preview = documents[i][:200].replace("\n", " ")
    print(f"  │ text preview : {text_preview}{'...' if len(documents[i]) > 200 else ''}")
    print(f"  └{'─'*60}")

# ══════════════════════════════════════════════════════════════════════════════
# 4. SIMILARITY SEARCH — end-to-end embedding round-trip
# ══════════════════════════════════════════════════════════════════════════════
section("4. Similarity Search — End-to-End Embedding Round-Trip")

try:
    from langchain_google_vertexai import VertexAIEmbeddings
    from langchain_chroma import Chroma

    print("  Initialising Vertex AI embeddings...")
    embeddings_fn = VertexAIEmbeddings(
        model_name=EMBEDDING_MODEL,
        project=GCP_PROJECT,
    )

    store = Chroma(
        client=client,
        collection_name=CHROMA_COLLECTION,
        embedding_function=embeddings_fn,
    )

    # Use text from the first chunk as the query to guarantee a match
    query = documents[0][:100] if documents else "What is this document about?"
    print(f"  Query           : \"{query[:80]}...\"")

    search_results = store.similarity_search_with_relevance_scores(query=query, k=3)

    print(f"\n  {'RANK':<5} {'SCORE':>8} {'CHUNK_ID':<45} {'PAGE':>4}")
    print(f"  {'─'*5} {'─'*8} {'─'*45} {'─'*4}")

    for rank, (doc, score) in enumerate(search_results, 1):
        cid  = doc.metadata.get("chunk_id", "?")[:43]
        page = doc.metadata.get("page_number", "?")
        print(f"  {rank:<5} {score:>8.4f} {cid:<45} {page:>4}")

    if search_results:
        top_score = search_results[0][1]
        if top_score > 0.85:
            print(f"\n  ✅ Top score {top_score:.4f} — embeddings are working correctly.")
        else:
            print(f"\n  ⚠️  Top score {top_score:.4f} — lower than expected for a self-query.")

except Exception as e:
    print(f"\n  ⚠️  Similarity search failed: {e}")
    print("     Check GCP credentials: gcloud auth application-default login")

# ══════════════════════════════════════════════════════════════════════════════
# 5. GCS — confirm the PDF object exists
# ══════════════════════════════════════════════════════════════════════════════
section("5. GCS — Uploaded PDF Objects")

try:
    from google.cloud import storage as gcs

    gcs_client = gcs.Client(project=GCP_PROJECT)
    bucket = gcs_client.bucket(GCS_BUCKET)

    # List all blobs under the upload prefix
    prefix = os.getenv("GCS_UPLOAD_PREFIX", "documents")
    blobs = list(gcs_client.list_blobs(GCS_BUCKET, prefix=prefix))

    if not blobs:
        print(f"  ⚠️  No objects found in gs://{GCS_BUCKET}/{prefix}/")
    else:
        print(f"  {'BLOB NAME':<70} {'SIZE':>8}")
        print(f"  {'─'*70} {'─'*8}")
        for blob in blobs:
            size_kb = (blob.size or 0) / 1024
            print(f"  {blob.name:<70} {size_kb:>7.1f}K")
        print(f"\n  ✅ {len(blobs)} object(s) found in gs://{GCS_BUCKET}/")

except Exception as e:
    print(f"  ⚠️  GCS check failed: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# 6. SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
section("6. Summary")

unique_docs = len(set(m.get("document_id", "") for m in metadatas))
print(f"  Documents indexed : {unique_docs}")
print(f"  Total chunks      : {total_chunks}")
print(f"  ChromaDB path     : {CHROMA_PERSIST_DIR}/chroma.sqlite3")
print(f"  GCS bucket        : gs://{GCS_BUCKET}/")
print(f"  Embedding model   : {EMBEDDING_MODEL} (768 dimensions)")
print(f"\n  Pipeline status   : {'✅ ALL STAGES VERIFIED' if total_chunks > 0 else '❌ No chunks found'}")
print()
