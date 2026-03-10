import os
from sqlmodel import create_engine, SQLModel, Session

# Import models so SQLModel knows they exist before creating tables
from models import RawComplaint, StructuredProblem

sqlite_file_name = "omoi.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# echo=False keeps the terminal clean from raw SQL logs
engine = create_engine(sqlite_url, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


# Automatically create the database file and tables when this runs
if __name__ == "__main__":
    create_db_and_tables()
    print("[*] SQLite database (omoi.db) initialized successfully!")
