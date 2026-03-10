from sqlmodel import Session, select
from database import engine, create_db_and_tables
from models import RawComplaint
from scrapers.reddit import fetch_reddit_complaints
from scrapers.hackernews import fetch_hn_complaints


def ingest_data():
    # Ensure tables exist
    create_db_and_tables()

    print("\n--- Starting Data Ingestion ---")

    # 1. Fetch raw data
    reddit_data = fetch_reddit_complaints(limit=50)
    hn_data = fetch_hn_complaints(hits_per_page=30)

    all_complaints = reddit_data + hn_data
    print(f"\n[*] Extracted {len(all_complaints)} potential complaints from the web.")

    # 2. Persist to SQLite securely
    new_inserts = 0
    with Session(engine) as session:
        for item in all_complaints:
            # Idempotency check: Does this URL already exist?
            existing = session.exec(
                select(RawComplaint).where(RawComplaint.url == item["url"])
            ).first()

            if not existing:
                complaint = RawComplaint(**item)
                session.add(complaint)
                new_inserts += 1

        session.commit()

    print(
        f"[*] Ingestion Complete! Added {new_inserts} new complaints to the database.\n"
    )


if __name__ == "__main__":
    ingest_data()
