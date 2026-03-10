import os
import re
from datetime import datetime, timezone
import praw
from dotenv import load_dotenv
from sqlmodel import Session, create_engine, select
from sqlalchemy.dialects.postgresql import insert

# Import the models we created in Step 1
from models import Source, Community, RawItem

load_dotenv()

# --- Configuration & Filters ---
DB_URL = os.getenv("DATABASE_URL")
engine = create_engine(DB_URL)

PAIN_PHRASES = [
    "biggest pain",
    "pain point",
    "struggling with",
    "the hardest part",
    "driving me crazy",
    "so frustrating",
    "headache",
]
WORKFLOW_PHRASES = [
    "takes me hours",
    "takes forever",
    "every week i have to",
    "every month we need to",
    "manually",
    "copy paste",
    "spreadsheet",
    "excel",
]
B2B_PHRASES = [
    "our clients",
    "b2b saas",
    "enterprise",
    "sales team",
    "account managers",
    "customer success",
    "csm",
    "lead gen",
    "pipeline",
    "demo calls",
    "onboarding",
    "renewals",
    "churn",
    "nps",
    "mrr",
    "arr",
    "agency",
]


def text_passes_filters(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()

    # Check if it has AT LEAST one pain/workflow phrase AND one B2B phrase
    has_pain = any(p in text_lower for p in PAIN_PHRASES + WORKFLOW_PHRASES)
    has_b2b = any(b in text_lower for b in B2B_PHRASES)

    return has_pain and has_b2b


# --- Database Helpers ---
def get_or_create_source(session: Session, name: str) -> Source:
    source = session.exec(select(Source).where(Source.name == name)).first()
    if not source:
        source = Source(name=name, details={"base_url": "https://reddit.com"})
        session.add(source)
        session.commit()
        session.refresh(source)
    return source


def get_or_create_community(
    session: Session, source_id: int, identifier: str
) -> Community:
    community = session.exec(
        select(Community).where(Community.identifier == identifier)
    ).first()
    if not community:
        community = Community(source_id=source_id, identifier=identifier)
        session.add(community)
        session.commit()
        session.refresh(community)
    return community


def upsert_raw_item(session: Session, item_dict: dict):
    # Postgres specific INSERT ON CONFLICT DO NOTHING
    stmt = insert(RawItem).values(**item_dict)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["source_id", "external_id", "type"]
    )
    session.exec(stmt)
    session.commit()


# --- Main Scraper Logic ---
def fetch_reddit_posts(
    subreddits: list[str], time_filter: str = "week", limit: int = 20
):
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT"),
    )

    with Session(engine) as session:
        source = get_or_create_source(session, "reddit")

        for sub_name in subreddits:
            print(f"[*] Scraping r/{sub_name}...")
            community = get_or_create_community(session, source.id, f"r/{sub_name}")
            subreddit = reddit.subreddit(sub_name)

            # Fetch top posts
            for submission in subreddit.top(time_filter=time_filter, limit=limit):
                # 1. Check the Post itself
                combined_text = f"{submission.title}\n{submission.selftext}"
                if text_passes_filters(combined_text):
                    print(f"  -> [MATCH POST] {submission.title[:50]}...")
                    post_item = {
                        "source_id": source.id,
                        "community_id": community.id,
                        "external_id": submission.id,
                        "type": "post",
                        "url": f"https://reddit.com{submission.permalink}",
                        "title": submission.title,
                        "body": submission.selftext,
                        "author": (
                            str(submission.author) if submission.author else "[deleted]"
                        ),
                        "score": submission.score,
                        "num_comments": submission.num_comments,
                        "created_utc": datetime.fromtimestamp(
                            submission.created_utc, tz=timezone.utc
                        ),
                        "fetched_at": datetime.now(timezone.utc),
                    }
                    upsert_raw_item(session, post_item)

                # 2. Check top comments (limit to top 10 to save API calls)
                submission.comment_sort = "top"
                submission.comments.replace_more(limit=0)  # Flatten comment tree

                for comment in submission.comments[:10]:
                    if text_passes_filters(comment.body):
                        print(f"  -> [MATCH COMMENT] {comment.body[:50]}...")
                        comment_item = {
                            "source_id": source.id,
                            "community_id": community.id,
                            "external_id": comment.id,
                            "type": "comment",
                            "url": f"https://reddit.com{comment.permalink}",
                            "title": None,
                            "body": comment.body,
                            "author": (
                                str(comment.author) if comment.author else "[deleted]"
                            ),
                            "score": comment.score,
                            "num_comments": 0,
                            "created_utc": datetime.fromtimestamp(
                                comment.created_utc, tz=timezone.utc
                            ),
                            "fetched_at": datetime.now(timezone.utc),
                        }
                        upsert_raw_item(session, comment_item)


if __name__ == "__main__":
    # Test it out on a single subreddit for the last week
    target_subs = ["SaaS", "Entrepreneur", "marketing"]
    fetch_reddit_posts(target_subs, time_filter="week", limit=20)
    print("[*] Ingestion complete.")
