import os
from typing import Optional, List, Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from openai import OpenAI
from sqlmodel import Session, select
from database import engine
from models import RawComplaint, StructuredProblem

# Load environment variables
load_dotenv()

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# --- 1. Strict Schema Definition ---
class StructuredProblemExtraction(BaseModel):
    is_valid_b2b_workflow: bool = Field(
        description="True ONLY if this complaint describes a professional, B2B, or software workflow pain point. False if it's about video games, politics, consumer goods, etc."
    )
    profession: Optional[str] = Field(
        description="The job title or role of the user (e.g., 'ecommerce manager', 'developer'). Null if unknown."
    )
    workflow: Optional[str] = Field(
        description="The specific process they are trying to complete (e.g., 'exporting reporting data'). Null if unknown."
    )
    pain_point: Optional[str] = Field(
        description="A concise summary of the core frustration or inefficiency."
    )
    tools_used: List[str] = Field(
        description="List of software tools explicitly mentioned (e.g., ['excel', 'salesforce']). Empty list if none."
    )
    frequency: Optional[Literal["daily", "weekly", "monthly", "unknown"]] = Field(
        description="How often this task seems to occur."
    )
    automation_potential: Optional[Literal["low", "medium", "high"]] = Field(
        description="How easily software could automate this manual process."
    )
    notes: Optional[str] = Field(
        description="Any extra context, particularly mentions of willingness to pay or current hacky workarounds."
    )


# --- 2. The System Prompt ---
SYSTEM_PROMPT = """
You are an expert B2B SaaS product manager. Your job is to read raw internet complaints and extract the underlying business workflow problems.
If the text is NOT a professional/B2B workflow problem (e.g., a joke, a consumer complaint, or generic chatter), set 'is_valid_b2b_workflow' to false and leave the rest null.
If it IS a valid workflow problem, extract the exact tools, frequency, and pain points described. Be concise and clinical.
"""


# --- 3. The Batch Processing Engine ---
def process_unstructured_complaints(batch_size: int = 50):
    print(f"\n--- Starting LLM Extraction (Batch Size: {batch_size}) ---")

    with Session(engine) as session:
        # Fetch complaints that haven't been structured yet
        subquery = select(StructuredProblem.raw_id)
        statement = (
            select(RawComplaint)
            .where(RawComplaint.id.not_in(subquery))
            .limit(batch_size)
        )
        unprocessed_items = session.exec(statement).all()

        if not unprocessed_items:
            print("[*] No new complaints to process. Everything is up to date!")
            return

        print(
            f"[*] Found {len(unprocessed_items)} unprocessed items. Sending to OpenAI..."
        )

        success_count = 0
        skipped_count = 0

        for item in unprocessed_items:
            try:
                # Prepare the payload
                user_text = f"Title: {item.title}\nBody: {item.text}"

                # Call OpenAI with Structured Outputs
                response = client.beta.chat.completions.parse(
                    model="gpt-4o-mini",  # Fast and incredibly cheap
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_text},
                    ],
                    response_format=StructuredProblemExtraction,
                )

                extraction = response.choices[0].message.parsed

                # If the LLM determined it's just noise, we still save a "null" record
                # so we don't process it again next time.
                if not extraction.is_valid_b2b_workflow:
                    skipped_count += 1
                    structured = StructuredProblem(
                        raw_id=item.id,
                        notes="[REJECTED BY LLM: Not a valid B2B workflow]",
                    )
                else:
                    # Map Pydantic object to SQLModel
                    success_count += 1
                    print(
                        f"  -> 💡 Found Problem: {extraction.profession} struggling with '{extraction.pain_point}'"
                    )
                    structured = StructuredProblem(
                        raw_id=item.id,
                        profession=extraction.profession,
                        workflow=extraction.workflow,
                        pain_point=extraction.pain_point,
                        tools_used=extraction.tools_used,
                        frequency=extraction.frequency,
                        automation_potential=extraction.automation_potential,
                        notes=extraction.notes,
                    )

                session.add(structured)
                session.commit()  # Commit one by one so if the script crashes, progress is saved

            except Exception as e:
                print(f"  [!] Error processing item {item.id}: {e}")
                session.rollback()

        print(
            f"\n[*] Extraction Complete! Extracted {success_count} valid workflows. Ignored {skipped_count} irrelevant posts."
        )


if __name__ == "__main__":
    process_unstructured_complaints()
