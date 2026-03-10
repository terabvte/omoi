import streamlit as st
import os
import faiss
import pickle
import numpy as np
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from sqlmodel import Session, select
from database import engine
from models import StructuredProblem

from dotenv import load_dotenv  # <--- ADD THIS

load_dotenv()  # <--- ADD THIS

st.title("💬 RAG Co-Founder")
st.markdown(
    "Ask questions about your database. E.g., *'What are founders complaining about regarding Stripe?'*"
)

# Initialize OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@st.cache_resource
def load_ml_assets():
    print("Loading ML models for RAG...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    try:
        index = faiss.read_index("ml/omoi_vectors.index")
        with open("ml/embeddings.pkl", "rb") as f:
            embedding_cache = pickle.load(f)
        return embedder, index, embedding_cache
    except Exception as e:
        print(f"Error loading FAISS: {e}")
        return embedder, None, None


embedder, index, embedding_cache = load_ml_assets()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Query your intelligence engine..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if not index:
            st.error("FAISS index not found. Run the pipeline first.")
        else:
            with st.spinner("Searching database..."):
                # 1. Embed user query
                query_vector = embedder.encode([prompt]).astype(np.float32)

                # 2. Search FAISS
                k = 10  # Retrieve top 10 relevant problems
                distances, indices = index.search(query_vector, k)
                retrieved_ids = indices[0].tolist()

                # 3. Fetch data from SQLite
                context_blocks = []
                with Session(engine) as session:
                    for db_id in retrieved_ids:
                        if db_id == -1:
                            continue  # FAISS padding if < k results
                        prob = session.exec(
                            select(StructuredProblem).where(
                                StructuredProblem.id == db_id
                            )
                        ).first()
                        if prob:
                            context_blocks.append(
                                f"[{prob.profession}] Workflow: {prob.workflow} | Pain: {prob.pain_point}"
                            )

                context_str = "\n".join(context_blocks)

                # 4. Generate Answer via OpenAI
                system_msg = (
                    "You are a strategic SaaS researcher. "
                    "Answer the user's question based ONLY on the following extracted pain points from our database:\n\n"
                    f"{context_str}\n\n"
                    "If the answer isn't in the provided context, say you don't have data on that yet."
                )

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt},
                    ],
                )

                answer = response.choices[0].message.content
                st.markdown(answer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer}
                )

                with st.expander("View Retrieved Database Context"):
                    st.write(context_str)
