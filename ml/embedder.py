import os
import pickle
import numpy as np
import faiss
from sqlmodel import Session, select
from sentence_transformers import SentenceTransformer
from database import engine
from models import StructuredProblem

# File paths for our local vector vault
EMBEDDINGS_FILE = "ml/embeddings.pkl"
FAISS_INDEX_FILE = "ml/omoi_vectors.index"

# Load local embedding model (downloads automatically on first run)
print("[*] Loading SentenceTransformer (all-MiniLM-L6-v2)...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")


def embed_new_problems():
    print("\n--- Starting Vector Embeddings ---")

    # 1. Load existing embeddings dictionary {db_id: vector}
    if os.path.exists(EMBEDDINGS_FILE):
        with open(EMBEDDINGS_FILE, "rb") as f:
            embedding_cache = pickle.load(f)
    else:
        embedding_cache = {}

    with Session(engine) as session:
        # Fetch all successfully parsed problems
        statement = select(StructuredProblem).where(
            StructuredProblem.profession != None
        )
        all_problems = session.exec(statement).all()

        # 2. Delta check: Find only the ones we haven't embedded yet
        new_problems = [p for p in all_problems if p.id not in embedding_cache]

        if not new_problems:
            print("[*] No new problems to embed. Skipping math.")
        else:
            print(
                f"[*] Found {len(new_problems)} new problems. Computing vectors locally..."
            )

            texts_to_embed = []
            for p in new_problems:
                # Combine fields into a dense context string
                text = f"Profession: {p.profession}. Workflow: {p.workflow}. Pain Point: {p.pain_point}."
                texts_to_embed.append(text)

            # Compute embeddings (returns a numpy array)
            embeddings = embedder.encode(texts_to_embed, show_progress_bar=True)

            # Update cache dictionary
            for p, emb in zip(new_problems, embeddings):
                embedding_cache[p.id] = emb

            # Save cache
            with open(EMBEDDINGS_FILE, "wb") as f:
                pickle.dump(embedding_cache, f)
            print(f"[*] Computed and cached {len(new_problems)} new embeddings.")

    # 3. Always rebuild the FAISS index so it stays perfectly in sync with DB
    if embedding_cache:
        print("[*] Building FAISS Index...")
        # FAISS requires IDs and vectors to be strictly separated but aligned arrays
        ids = np.array(list(embedding_cache.keys()), dtype=np.int64)
        vectors = np.array(list(embedding_cache.values()), dtype=np.float32)

        # Create a blank L2 index based on MiniLM's 384 dimensions
        dimension = vectors.shape[1]
        base_index = faiss.IndexFlatL2(dimension)

        # Wrap it in an IDMap so we can query it later to get actual SQLite DB IDs back
        index = faiss.IndexIDMap(base_index)
        index.add_with_ids(vectors, ids)

        faiss.write_index(index, FAISS_INDEX_FILE)
        print(f"[*] FAISS vector vault secured on disk ({index.ntotal} vectors).")


if __name__ == "__main__":
    embed_new_problems()
