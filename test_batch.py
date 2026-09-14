import os
# Read API key from environment variable
if 'GEMINI_API_KEY' not in os.environ:
    os.environ['GEMINI_API_KEY'] = ''
from google import genai
from pydantic import BaseModel
import json
from google.genai import types

client = genai.Client()

class FinalRecommendation(BaseModel):
    request_id: str
    amount_safe_to_pay: float
    affordability_status: str
    recommended_payment_method: str
    payment_plan: str
    earliest_date_for_full_payment: str
    spending_changes_needed: str
    decision_explanation: str

class BatchDecision(BaseModel):
    decisions: list[FinalRecommendation]

contexts = [
    "Request 1: 50 USD, balance 100",
    "Request 2: 200 USD, balance 50"
]
prompt = "Generate decisions for the following requests. Return a list in the same order.\n"
for i, c in enumerate(contexts):
    prompt += f"--- Context {i} ---\n{c}\n"

response = client.models.generate_content(
    model='gemini-3.6-flash',
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=BatchDecision,
        temperature=0.0
    )
)
print(response.text)
