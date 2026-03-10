import streamlit as st
from sqlmodel import Session, select
from database import engine
from models import ProblemCluster, StructuredProblem, RawComplaint

st.title("🔬 Cluster Explorer")

with Session(engine) as session:
    clusters = session.exec(
        select(ProblemCluster).order_by(ProblemCluster.opportunity_score.desc())
    ).all()

    if not clusters:
        st.warning("No clusters available. Run your pipeline!")
        st.stop()

    cluster_ids = [c.cluster_id for c in clusters]
    selected_id = st.selectbox("Select a Cluster ID to investigate:", cluster_ids)

    # Get the specific cluster metadata
    cluster_meta = next((c for c in clusters if c.cluster_id == selected_id), None)

    st.subheader(f"Metrics for Cluster {selected_id}")
    col1, col2 = st.columns(2)
    col1.metric("Opportunity Score", f"{cluster_meta.opportunity_score:.1f}")
    col2.metric("Total Complaints", cluster_meta.item_count)

    st.divider()
    st.subheader("The Evidence Locker")

    # Join StructuredProblem with RawComplaint to show the full context
    statement = (
        select(StructuredProblem, RawComplaint)
        .join(RawComplaint)
        .where(StructuredProblem.cluster_id == selected_id)
    )
    results = session.exec(statement).all()

    for structured, raw in results:
        with st.container():
            st.markdown(f"**Target User:** `{structured.profession}`")
            st.markdown(f"**Workflow:** {structured.workflow}")
            st.markdown(f"**Pain Point:** {structured.pain_point}")

            # Show tools as a badge/tag if they exist
            if structured.tools_used:
                tools = ", ".join(structured.tools_used)
                st.markdown(f"**Tools:** `{tools}`")
            else:
                st.markdown("**Tools:** `None mentioned`")

            with st.expander("View Original Source Text"):
                if raw.title:
                    st.write(f"**{raw.title}**")
                st.write(raw.text)
                st.markdown(f"[Source URL]({raw.url})")
            st.markdown("---")
