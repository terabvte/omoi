import pandas as pd
from sqlalchemy import create_engine
import textwrap
import html
import re

# Connect to the database
engine = create_engine("sqlite:///omoi.db")
df = pd.read_sql(
    "SELECT source, community, title, text, url, upvotes FROM raw_complaints", engine
)

# Calculate word count to filter out tiny generic replies
df["word_count"] = df["text"].apply(lambda x: len(str(x).split()))
df = df[df["word_count"] > 30]


# Clean up Hacker News HTML tags and entities (e.g., &#x27; -> ', <p> -> newline)
def clean_text(text):
    if not text:
        return ""
    text = html.unescape(text)  # Fixes &#x27; and &quot;
    text = re.sub(r"<[^>]+>", "\n", text)  # Removes <p>, <a>, <i>, etc.
    text = re.sub(r"\n\s*\n", "\n\n", text)  # Cleans up multiple newlines
    return text.strip()


df["text"] = df["text"].apply(clean_text)

# Split into dataframes
reddit_df = df[df["source"] == "reddit"]
hn_df = df[df["source"] == "hackernews"]


def print_complaint(row):
    print(
        f"\n[{row['source'].upper()}] {row['community']} | 💬 {row['word_count']} words | ⬆️ {row['upvotes']} upvotes"
    )
    if pd.notna(row["title"]) and row["title"]:
        print(f"📌 TITLE: {row['title']}")

    wrapped_text = textwrap.fill(
        row["text"], width=90, max_lines=7, placeholder=" ... [Read More in DB]"
    )
    print(f"\n{wrapped_text}\n")
    print(f"🔗 {row['url']}")
    print("-" * 60)


print("\n" + "=" * 60)
print(" 🎲 UNBIASED RANDOM SAMPLER (5 Reddit, 5 Hacker News)")
print("=" * 60)

print("\n--- 🔴 REDDIT SAMPLES ---")
if not reddit_df.empty:
    sample_size = min(5, len(reddit_df))
    for _, row in reddit_df.sample(n=sample_size).iterrows():
        print_complaint(row)

print("\n--- 🟠 HACKER NEWS SAMPLES ---")
if not hn_df.empty:
    sample_size = min(5, len(hn_df))
    for _, row in hn_df.sample(n=sample_size).iterrows():
        print_complaint(row)
