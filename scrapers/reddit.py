import time
import random
import requests
from datetime import datetime, timezone

TARGET_SUBS = [
    # Founder / SaaS communities
    "startups",
    "Entrepreneur",
    "SaaS",
    "EntrepreneurRideAlong",
    "indiehackers",
    "SideProject",
    "smallbusiness",
    "freelance",
    "consulting",
    # Technical operators (high SaaS signal)
    "sysadmin",
    "devops",
    "programming",
    "webdev",
    "dataengineering",
    "dataanalysis",
    "analytics",
    "ITManagers",
    "Database",
    "cloudcomputing",
    # Marketing & growth operators
    "marketing",
    "digital_marketing",
    "PPC",
    "SEO",
    "content_marketing",
    "growthhacking",
    "emailmarketing",
    # Ecommerce operators
    "ecommerce",
    "shopify",
    "AmazonSeller",
    "FulfillmentByAmazon",
    "dropshipping",
    # Sales & CRM operators
    "sales",
    "CRM",
    "salesops",
    # Finance & accounting workflows
    "accounting",
    "Bookkeeping",
    "finance",
    "FinancialCareers",
    # Operations / project management
    "adops",
    "projectmanagement",
    "supplychain",
    "logistics",
    # AI workflow communities (very strong signals right now)
    "ChatGPT",
    "ArtificialInteligence",
    "OpenAI",
    "PromptEngineering",
    "LangChain",
]

MANUAL_WORK = [
    "manual",
    "manually",
    "manual process",
    "copy paste",
    "copy-paste",
    "copying and pasting",
    "data entry",
    "hand enter",
    "entering data",
    "retyping",
    "tedious",
    "repetitive task",
    "repetitive work",
]

TIME_PAIN = [
    "takes hours",
    "takes forever",
    "time consuming",
    "waste of time",
    "hours every week",
    "every day",
    "every week",
    "every month",
    "spend hours",
    "takes too long",
]

DATA_WORK = [
    "spreadsheet",
    "excel",
    "google sheets",
    "csv",
    "export csv",
    "cleaning data",
    "data cleanup",
    "data formatting",
    "merge spreadsheets",
    "duplicate rows",
    "data normalization",
]

WORKFLOW = [
    "workflow",
    "pipeline",
    "process",
    "automation",
    "automate",
    "automating",
    "automated",
    "workflow automation",
    "manual workflow",
]

DATA_TRANSFER = [
    "export",
    "import",
    "export data",
    "import data",
    "export to excel",
    "export to csv",
    "import csv",
    "sync data",
    "data sync",
]

TOOL_GAPS = [
    "why is there no tool",
    "no tool for",
    "looking for tool",
    "better tool",
    "alternative to",
    "tool recommendation",
    "does a tool exist",
    "wish there was a tool",
]

WORKAROUNDS = [
    "workaround",
    "hacky solution",
    "hacky workaround",
    "custom script",
    "python script",
    "bash script",
    "quick script",
    "script I wrote",
    "internal tool",
]

INTEGRATION = [
    "integrate",
    "integration",
    "api integration",
    "connect tools",
    "tool integration",
    "sync tools",
    "bridge between",
]

AUTOMATION_TOOLS = [
    "zapier",
    "make.com",
    "n8n",
    "automation script",
    "workflow automation",
    "automate this",
]

AI_WORKFLOW = [
    "paste into chatgpt",
    "chatgpt workflow",
    "ai prompt",
    "prompt template",
    "prompt library",
    "prompt workflow",
    "using chatgpt for",
]

COMPLAINT_PHRASES = [
    "I hate doing",
    "I hate this process",
    "this is annoying",
    "this sucks",
    "so annoying",
    "pain in the ass",
    "frustrating workflow",
    "terrible workflow",
]

KEYWORDS = (
    MANUAL_WORK
    + TIME_PAIN
    + DATA_WORK
    + WORKFLOW
    + DATA_TRANSFER
    + TOOL_GAPS
    + WORKAROUNDS
    + INTEGRATION
    + AUTOMATION_TOOLS
    + AI_WORKFLOW
    + COMPLAINT_PHRASES
)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
]


def text_passes_filters(text: str) -> bool:
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in KEYWORDS)


def fetch_reddit_complaints(limit: int = 50) -> list[dict]:
    results = []

    for sub in TARGET_SUBS:
        print(f"[*] Scraping Reddit: r/{sub}...")
        url = f"https://www.reddit.com/r/{sub}/new.json?limit={limit}"
        headers = {"User-Agent": random.choice(USER_AGENTS)}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})

                title = post.get("title", "")
                selftext = post.get("selftext", "")
                combined_text = f"{title}\n{selftext}"

                if text_passes_filters(combined_text):
                    results.append(
                        {
                            "source": "reddit",
                            "community": f"r/{sub}",
                            "content_type": "post",
                            "author": post.get("author", "unknown"),
                            "date": datetime.fromtimestamp(
                                post.get("created_utc", 0), tz=timezone.utc
                            ),
                            "title": title,
                            "text": selftext,
                            "url": f"https://reddit.com{post.get('permalink', '')}",
                            "upvotes": post.get("score", 0),
                            "num_comments": post.get("num_comments", 0),
                        }
                    )
        except Exception as e:
            print(f"    [!] Failed to fetch r/{sub}: {e}")

        # Respect Reddit's rate limits
        time.sleep(2)

    return results
