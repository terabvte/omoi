from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, Column, String, JSON
from sqlalchemy import UniqueConstraint, Index
from datetime import datetime, timezone

# --- 1. Sources ---
class Source(SQLModel, table=True):
    __tablename__ = "sources"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True) # e.g., "reddit", "indiehackers"
    details: dict = Field(default={}, sa_column=Column(JSON))

# --- 2. Communities ---
class Community(SQLModel, table=True):
    __tablename__ = "communities"
    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="sources.id")
    identifier: str # e.g., "r/SaaS"
    is_active: bool = Field(default=True)

# --- 3. Raw Items ---
class RawItem(SQLModel, table=True):
    __tablename__ = "raw_items"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", "type", name="uq_raw_item"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="sources.id")
    community_id: int = Field(foreign_key="communities.id")
    external_id: str = Field(index=True)
    type: str # "post" or "comment"
    url: str
    title: Optional[str] = None
    body: str
    author: str
    score: int = Field(default=0)
    num_comments: Optional[int] = Field(default=0)
    created_utc: datetime
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# --- 4. Pain Points ---
class PainPoint(SQLModel, table=True):
    __tablename__ = "pain_points"

    id: Optional[int] = Field(default=None, primary_key=True)
    raw_item_id: int = Field(foreign_key="raw_items.id", unique=True)

    is_b2b: bool = Field(index=True)
    actor_role: Optional[str] = None
    company_type: Optional[str] = None
    pain_summary: Optional[str] = None
    pain_category: Optional[str] = Field(default=None, index=True)
    current_workaround: Optional[str] = None
    recurrence: Optional[str] = None # daily, weekly, monthly, one_off, unclear
    severity_1_to_10: Optional[int] = Field(default=None, index=True)
    willingness_to_pay_signal: bool = Field(default=False)

    # Store lists as JSON
    mentions_tool_names: List[str] = Field(default=[], sa_column=Column(JSON))
    saas_opportunity_comment: Optional[str] = None

    llm_model: str
    llm_called_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# --- 5. Pain Clusters (V2 Design) ---
class PainCluster(SQLModel, table=True):
    __tablename__ = "pain_clusters"

    id: Optional[int] = Field(default=None, primary_key=True)
    label: str
    description: Optional[str] = None
    pain_category: Optional[str] = None
    avg_severity: float = Field(default=0.0)
    item_count: int = Field(default=0)

# --- 6. Pain Cluster Items (Join Table) ---
class PainClusterItem(SQLModel, table=True):
    __tablename__ = "pain_cluster_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    cluster_id: int = Field(foreign_key="pain_clusters.id")
    pain_point_id: int = Field(foreign_key="pain_points.id")
    similarity_score: float = Field(default=0.0)
