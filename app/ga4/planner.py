import json
import os
from openai import OpenAI
from app.ga4.field_allowlist import ALLOWED_METRICS, ALLOWED_DIMENSIONS
from app.utils.date_parser import parse_date_range


def plan_report(query: str) -> dict:
    """
    Converts a natural-language query into a GA4 RunReportRequest-compatible plan.
    """

    client = OpenAI(
        base_url=os.getenv("LITELLM_BASE_URL", "http://3.110.18.218"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    system_prompt = f"""
You are a GA4 Report Planner.

Allowed metrics:
{list(ALLOWED_METRICS)}

Allowed dimensions:
{list(ALLOWED_DIMENSIONS)}

Return ONLY valid JSON in this format:

{{
  "metrics": ["totalUsers"],
  "dimensions": ["date"],
  "date_range_phrase": "last 7 days"
}}

Rules:
- Use ONLY allowed fields
- Default date_range_phrase to "last 7 days"
- No explanations, JSON only
"""

    try:
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            temperature=0,
        )

        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        raw_plan = json.loads(content)

    except Exception:
        raw_plan = {
            "metrics": ["totalUsers"],
            "dimensions": [],
            "date_range_phrase": "last 7 days",
        }

    # Date handling
    try:
        parsed_range = parse_date_range(raw_plan.get("date_range_phrase", "last 7 days"))
    except Exception:
        parsed_range = parse_date_range("last 7 days")

    return {
        "metrics": [{"name": m} for m in raw_plan.get("metrics", []) if m in ALLOWED_METRICS],
        "dimensions": [{"name": d} for d in raw_plan.get("dimensions", []) if d in ALLOWED_DIMENSIONS],
        "date_ranges": [
            {
                "start_date": parsed_range["start_date"],
                "end_date": parsed_range["end_date"],
            }
        ],
    }
