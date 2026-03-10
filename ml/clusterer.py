import pickle
import numpy as np
from sklearn.cluster import HDBSCAN
from sqlmodel import Session, select
from database import engine
from models import StructuredProblem

EMBEDDINGS_FILE = "ml/embeddings.pkl"


def cluster_problems():
    print("\n--- Starting Unsupervised Clustering ---")

    try:
        with open(EMBEDDINGS_FILE, "rb") as f:
            embedding_cache = pickle.load(f)
    except FileNotFoundError:
        print("[!] No embeddings found. Skipping clustering.")
        return

    if len(embedding_cache) < 10:
        print("[*] Not enough data points to form meaningful clusters yet. Skipping.")
        return

    # 1. Prepare data for scikit-learn
    ids = np.array(list(embedding_cache.keys()))
    vectors = np.array(list(embedding_cache.values()))

    print(f"[*] Running HDBSCAN algorithm on {len(vectors)} vectors...")

    # 2. Run HDBSCAN
    # min_cluster_size=2 means we need at least 2 people complaining about the exact same thing to call it a "market"
    clusterer = HDBSCAN(
        min_cluster_size=2, min_samples=1, metric="euclidean", copy=True
    )
    labels = clusterer.fit_predict(vectors)

    unique_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    noise_points = list(labels).count(-1)
    print(f"[*] AI identified {unique_clusters} distinct B2B problem clusters.")
    print(f"[*] Ignored {noise_points} distinct outliers as 'noise'.")

    # 3. Update the SQLite Database
    print("[*] Saving cluster assignments to database...")
    with Session(engine) as session:
        # Fetch all structured problems we just clustered
        statement = select(StructuredProblem).where(
            StructuredProblem.id.in_(ids.tolist())
        )
        db_problems = session.exec(statement).all()

        # Create a fast lookup dictionary: db_id -> cluster_label
        label_map = {int(db_id): int(label) for db_id, label in zip(ids, labels)}

        for p in db_problems:
            cluster_id = label_map.get(p.id, -1)
            # -1 in HDBSCAN means "noise/no cluster". We map that back to None in the database.
            p.cluster_id = cluster_id if cluster_id != -1 else None

        session.commit()
        print("[*] Clustering Complete! SQLite `structured_problems` updated.")


if __name__ == "__main__":
    cluster_problems()
