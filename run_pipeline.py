from run_ingestion import ingest_data
from ml.llm_extractor import process_unstructured_complaints
from ml.embedder import embed_new_problems
from ml.clusterer import cluster_problems


def main():
    print("🚀 INITIALIZING OMOI PIPELINE 🚀")

    # Step 1: Scrape new data
    ingest_data()

    # Step 2: Extract JSON logic
    process_unstructured_complaints(batch_size=50)

    # Step 3 & 4: The Intelligence Layers
    embed_new_problems()
    cluster_problems()

    print("\n✅ PIPELINE RUN FINISHED.")


if __name__ == "__main__":
    main()
