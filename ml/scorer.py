import pandas as pd
from sqlmodel import Session, select
from database import engine, create_db_and_tables
from models import StructuredProblem, ProblemCluster

# Hardcoded business logic weights
FREQ_MAP = {"daily": 3, "weekly": 2, "monthly": 1, "unknown": 0}
AUTO_MAP = {"high": 3, "medium": 2, "low": 1, "unknown": 0}


def score_clusters():
    print("\n--- Starting Opportunity Scoring ---")

    # Ensure the new ProblemCluster table is created in SQLite
    create_db_and_tables()

    with Session(engine) as session:
        # 1. Fetch only problems that were successfully clustered
        statement = select(StructuredProblem).where(
            StructuredProblem.cluster_id != None
        )
        problems = session.exec(statement).all()

        if not problems:
            print("[*] No clustered problems found to score.")
            return

        # 2. Convert database rows into a fast Pandas DataFrame
        data = []
        for p in problems:
            data.append(
                {
                    "cluster_id": p.cluster_id,
                    "freq_score": FREQ_MAP.get(p.frequency, 0) if p.frequency else 0,
                    "auto_score": (
                        AUTO_MAP.get(p.automation_potential, 0)
                        if p.automation_potential
                        else 0
                    ),
                }
            )

        df = pd.DataFrame(data)

        # 3. Group by cluster and calculate averages/counts
        agg_df = (
            df.groupby("cluster_id")
            .agg(
                item_count=("cluster_id", "count"),
                avg_freq=("freq_score", "mean"),
                avg_auto=("auto_score", "mean"),
            )
            .reset_index()
        )

        # 4. The Opportunity Formula
        # We reward clusters that have a high volume of complaints (size multiplier)
        agg_df["opportunity_score"] = (
            agg_df["avg_freq"] + agg_df["avg_auto"] + (agg_df["item_count"] * 0.5)
        )

        # Sort highest score to the top
        agg_df = agg_df.sort_values(by="opportunity_score", ascending=False)

        print(f"[*] Evaluated and scored {len(agg_df)} distinct markets.")

        # 5. Persist the scores back to SQLite
        for _, row in agg_df.iterrows():
            cluster_id = int(row["cluster_id"])

            # Upsert logic: Update if it exists, insert if it doesn't
            existing = session.exec(
                select(ProblemCluster).where(ProblemCluster.cluster_id == cluster_id)
            ).first()

            if existing:
                existing.opportunity_score = row["opportunity_score"]
                existing.item_count = int(row["item_count"])
                session.add(existing)
            else:
                new_cluster = ProblemCluster(
                    cluster_id=cluster_id,
                    opportunity_score=row["opportunity_score"],
                    item_count=int(row["item_count"]),
                    cluster_name=f"Cluster {cluster_id}",  # Placeholder until Step 6
                )
                session.add(new_cluster)

        session.commit()

        # 6. Print the Leaderboard
        print("\n🏆 TOP 3 MICRO-SAAS OPPORTUNITIES 🏆")
        for index, row in agg_df.head(3).iterrows():
            print(
                f"Cluster {int(row['cluster_id'])} | Score: {row['opportunity_score']:.1f} | Complaints: {int(row['item_count'])}"
            )
        print("-----------------------------------")


if __name__ == "__main__":
    score_clusters()
