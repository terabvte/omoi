import pandas as pd
from sqlalchemy import create_engine
import textwrap
import random

# Connect to the database
engine = create_engine("sqlite:///omoi.db")
df = pd.read_sql(
    "SELECT source, community, title, text, url, upvotes FROM raw_complaints", engine
)
df["word_count"] = df["text"].apply(lambda x: len(str(x).split()))

# Filter out the absolute junk
df = df[df["word_count"] > 30]

reddit_df = df[df["source"] == "reddit"]
hn_df = df[df["source"] == "hackernews"]


def print_complaint(row, title_prefix=""):
    print(
        f"\n[{row['source'].upper()}] {row['community']} | 💬 {row['word_count']} words | ⬆️ {row['upvotes']} points"
    )
    if pd.notna(row["title"]) and row["title"]:
        print(f"📌 TITLE: {row['title']}")

    wrapped_text = textwrap.fill(
        row["text"], width=90, max_lines=6, placeholder=" ... [Read More in DB]"
    )
    print(f"\n{wrapped_text}\n")
    print(f"🔗 {row['url']}")
    print("-" * 60)


print("\n" + "=" * 60)
print(" 🔴 TOP 3 REDDIT COMPLAINTS (By Upvotes)")
print("=" * 60)
for _, row in reddit_df.sort_values(by="upvotes", ascending=False).head(3).iterrows():
    print_complaint(row)

print("\n" + "=" * 60)
print(" 🟠 TOP 3 HACKER NEWS COMPLAINTS (By Points)")
print("=" * 60)
for _, row in hn_df.sort_values(by="upvotes", ascending=False).head(3).iterrows():
    print_complaint(row)

print("\n" + "=" * 60)
print(" 🟢 3 RANDOM H.N. 'DEEP CUTS' (100 - 300 words)")
print(" (This is usually where the boring B2B workflow gold hides)")
print("=" * 60)
# Filter for Goldilocks length (not too short, not a whole manifesto)
deep_cuts = hn_df[(hn_df["word_count"] >= 100) & (hn_df["word_count"] <= 300)]
if not deep_cuts.empty:
    sample_size = min(3, len(deep_cuts))
    for _, row in deep_cuts.sample(n=sample_size).iterrows():
        print_complaint(row)
else:
    print("Not enough deep cuts found.")
