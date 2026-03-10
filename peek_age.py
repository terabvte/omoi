import pandas as pd
from sqlalchemy import create_engine

# 1. Load the data
engine = create_engine("sqlite:///omoi.db")
df = pd.read_sql("SELECT source, date FROM raw_complaints", engine)

# 2. Calculate age in days
df["date"] = pd.to_datetime(df["date"], utc=True)
now = pd.Timestamp.now(tz="UTC")
df["age_days"] = (now - df["date"]).dt.days

# 3. Categorize into time buckets
bins = [-1, 30, 90, 365, 1095, 10000]
labels = ["< 1 Month", "1-3 Months", "3-12 Months", "1-3 Years", "3+ Years"]
df["age_bucket"] = pd.cut(df["age_days"], bins=bins, labels=labels)

# 4. Print the distribution table
print("\n📊 AGE DISTRIBUTION BY SOURCE (Post Count) 📊\n")
distribution = (
    df.groupby(["source", "age_bucket"], observed=False).size().unstack(fill_value=0)
)
print(distribution)

print("\n--- AVERAGE AGE ---")
print(df.groupby("source")["age_days"].mean().round(1).astype(str) + " days old")
print("-------------------\n")
