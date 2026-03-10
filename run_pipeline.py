from run_ingestion import ingest_data
from ml.llm_extractor import process_unstructured_complaints


def main():
    print("🚀 INITIALIZING OMOI PIPELINE 🚀")

    # Step 1: Scrape new data from the internet
    ingest_data()

    # Step 2: Pass new data to the LLM for structuring
    # You can increase batch_size once you know it works. 50 costs roughly $0.01 on gpt-4o-mini.
    process_unstructured_complaints(batch_size=50)

    print("\n✅ PIPELINE RUN FINISHED.")


if __name__ == "__main__":
    main()
