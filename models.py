from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column, JSON


class RawComplaint(SQLModel, table=True):
    __tablename__ = "raw_complaints"

    id: Optional[int] = Field(default=None, primary_key=True)
    source: str = Field(index=True)  # "reddit" or "hackernews"
    community: Optional[str] = None  # e.g., "r/SaaS"
    content_type: str = Field(default="post")  # "post" or "comment"
    author: str
    date: datetime
    title: Optional[str] = None
    text: str
    url: str = Field(unique=True, index=True)
    upvotes: int = Field(default=0)
    num_comments: int = Field(default=0)


class StructuredProblem(SQLModel, table=True):
    __tablename__ = "structured_problems"

    id: Optional[int] = Field(default=None, primary_key=True)
    raw_id: int = Field(foreign_key="raw_complaints.id", unique=True)

    profession: Optional[str] = None
    workflow: Optional[str] = None
    pain_point: Optional[str] = None

    tools_used: List[str] = Field(default=[], sa_column=Column(JSON))

    frequency: Optional[str] = None
    automation_potential: Optional[str] = None
    notes: Optional[str] = None

    cluster_id: Optional[int] = Field(default=None, index=True)


class ProblemCluster(SQLModel, table=True):
    __tablename__ = "problem_clusters"

    cluster_id: int = Field(primary_key=True)
    opportunity_score: float = Field(default=0.0)
    item_count: int = Field(default=0)

    # We will generate this with an LLM in the Streamlit step,
    # but we need the column ready now.
    cluster_name: Optional[str] = None
