import streamlit as st
import pandas as pd
from sqlmodel import Session, select
from database import engine
from models import ProblemCluster, RawComplaint

st.title("📊 Market Leaderboard")

with Session(engine) as session:
    # Fetch clusters sorted by score
    clusters = session.exec(
        select(ProblemCluster).order_by(ProblemCluster.opportunity_score.desc())
    ).all()

    if clusters:
        df = pd.DataFrame([c.dict() for c in clusters])
        st.dataframe(
            df[["cluster_id", "opportunity_score", "item_count", "cluster_name"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No clusters formed yet. Run your pipeline to generate data.")

st.divider()

st.title("📰 Raw Intelligence Feed")
st.markdown(
    "Read the unedited complaints from founders and developers to build raw empathy."
)

with Session(engine) as session:
    raw_feed = session.exec(
        select(RawComplaint).order_by(RawComplaint.date.desc()).limit(50)
    ).all()

    for item in raw_feed:
        with st.expander(
            f"[{item.source.upper()}] {item.community} - {item.date.strftime('%Y-%m-%d')} (⬆️ {item.upvotes})"
        ):
            if item.title:
                st.write(f"**{item.title}**")
            st.write(item.text)
            st.markdown(f"[Link to original post]({item.url})")
