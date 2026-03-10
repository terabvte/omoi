from run_ingestion import ingest_data
from ml.llm_extractor import process_unstructured_complaints
from ml.embedder import embed_new_problems
from ml.clusterer import cluster_problems
from ml.scorer import score_clusters


def main():
    print("🚀 INITIALIZING OMOI PIPELINE 🚀")

    ingest_data()
    process_unstructured_complaints(batch_size=50)
    embed_new_problems()
    cluster_problems()

    # Step 5: Score and rank the markets
    score_clusters()

    print("\n✅ PIPELINE RUN FINISHED.")


if __name__ == "__main__":
    main()
