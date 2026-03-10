import requests
import time
from datetime import datetime, timezone

KEYWORDS = [
    "manual",
    "manually",
    "manual process",
    "manual workflow",
    "manual task",
    "copy paste",
    "copy-paste",
    "copying and pasting",
    "data entry",
    "retyping",
    "re-enter data",
    "reenter data",
    "tedious",
    "repetitive task",
    "repetitive work",
    "doing this by hand",
    "takes hours",
    "takes forever",
    "time consuming",
    "waste of time",
    "hours every week",
    "spend hours",
    "spend too much time",
    "takes too long",
    "too much time spent",
    "spreadsheet",
    "spreadsheets",
    "excel",
    "google sheets",
    "csv",
    "export csv",
    "import csv",
    "cleaning data",
    "data cleanup",
    "data cleaning",
    "data formatting",
    "merge spreadsheets",
    "duplicate rows",
    "data normalization",
    "data transformation",
    "workflow",
    "workflow problem",
    "workflow friction",
    "pipeline",
    "process",
    "internal process",
    "process automation",
    "automation opportunity",
    "why is there no tool",
    "no tool for this",
    "missing tool",
    "tool gap",
    "looking for a tool",
    "does a tool exist",
    "wish there was a tool",
    "better tool for",
    "alternative to",
    "quick script",
    "hacky script",
    "custom script",
    "python script",
    "bash script",
    "small script",
    "script I wrote",
    "internal tool",
    "internal dashboard",
    "temporary script",
    "api integration",
    "api problem",
    "api limitation",
    "integrate with",
    "integration problem",
    "connect tools",
    "data sync",
    "sync tools",
    "bridge between",
    "export data",
    "import data",
    "export to excel",
    "export to csv",
    "import into spreadsheet",
    "data export",
    "data import",
    "moving data between",
    "zapier",
    "make.com",
    "n8n",
    "airtable automation",
    "workflow automation",
    "automate this",
    "automation tool",
    "report generation",
    "manual reporting",
    "build reports",
    "export reports",
    "analytics pipeline",
    "data pipeline",
    "report automation",
    "paste into chatgpt",
    "chatgpt workflow",
    "ai prompt",
    "prompt template",
    "prompt library",
    "ai workflow",
    "ai automation",
    "manual ai workflow",
    "I hate doing",
    "this sucks",
    "so annoying",
    "frustrating workflow",
    "terrible workflow",
    "pain in the ass",
    "tooling sucks",
    "developer tooling",
    "dev tooling",
    "bad tooling",
    "tooling gap",
    "missing feature",
    "switched from",
    "migrating from",
    "replacing tool",
    "tool replacement",
    "looking for alternative",
    "doesn't scale",
    "scaling problem",
    "hard to scale",
    "brittle workflow",
    "fragile system",
    "technical debt",
    "maintenance burden",
]


def fetch_hn_complaints(hits_per_page: int = 20) -> list[dict]:
    results = []
    base_url = "http://hn.algolia.com/api/v1/search"

    # Calculate the Unix timestamp for 1 year ago (365 days)
    one_year_ago = int(time.time()) - (365 * 24 * 60 * 60)

    for kw in KEYWORDS:
        print(f"[*] Scraping Hacker News for keyword: '{kw}'...")
        params = {
            "query": kw,
            "tags": "comment",
            "hitsPerPage": hits_per_page,
            "numericFilters": f"created_at_i>{one_year_ago}",  # <-- THE FIX
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            for hit in data.get("hits", []):
                text = hit.get("comment_text", "")
                if text:
                    created_at_str = hit.get("created_at")
                    dt = (
                        datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        if created_at_str
                        else datetime.now(timezone.utc)
                    )

                    results.append(
                        {
                            "source": "hackernews",
                            "community": "Hacker News",
                            "content_type": "comment",
                            "author": hit.get("author", "unknown"),
                            "date": dt,
                            "title": hit.get("story_title", ""),
                            "text": text,
                            "url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                            "upvotes": hit.get("points", 0) or 0,
                            "num_comments": 0,
                        }
                    )
        except Exception as e:
            print(f"    [!] Failed to fetch HN keyword '{kw}': {e}")

    return results
