import json
from app.llm import call_llm

def plan_seo_query(query: str, columns: list[str]) -> dict:
    """
    Converts a natural language query into a structured execution plan using LLM.
    """
    
    system_prompt = (
        "You are an SEO Data Analyst. Convert the user's natural language query into a structured JSON execution plan.\n"
        "You have a dataset with the following columns (all lowercase):\n"
        f"{json.dumps(columns)}\n\n"
        "### Plan Schema\n"
        "Return a JSON object with these keys:\n"
        "1. 'filters': List of { 'column': str, 'operator': str, 'value': any }.\n"
        "   - Operators: '==', '!=', '>', '<', '>=', '<=', 'contains', 'not_contains', 'is_null', 'is_not_null'.\n"
        "2. 'group_by': Column name to group by (optional, null if none).\n"
        "3. 'aggregations': List of { 'column': str, 'metric': str }.\n"
        "   - Metrics: 'count', 'sum', 'mean', 'min', 'max', 'unique_count', 'list'.\n"
        "   - If 'group_by' is null, these are global aggregations.\n"
        "   - If 'group_by' is set, these are calculated per group.\n"
        "4. 'sort': { 'column': str, 'ascending': bool } (optional).\n"
        "5. 'limit': int (optional, default 100).\n"
        "6. 'calculated_fields': List of { 'name': str, 'expression': str } (optional).\n"
        "   - Simple arithmetic or boolean logic if needed (e.g. 'indexable_ratio').\n"
        "   - NOTE: Keep this simple. If complex, prefer standard aggregations.\n\n"
        "### Examples\n"
        "Q: 'Which URLs have status 200?'\n"
        "A: { \"filters\": [{ \"column\": \"status code\", \"operator\": \"==\", \"value\": 200 }], \"limit\": 100 }\n\n"
        "Q: 'Count of pages by indexability'\n"
        "A: { \"group_by\": \"indexability\", \"aggregations\": [{ \"column\": \"address\", \"metric\": \"count\" }] }\n\n"
        "Q: 'Pages with title length > 60'\n"
        "A: { \"filters\": [{ \"column\": \"title 1 length\", \"operator\": \">\", \"value\": 60 }] }\n\n"
        "### Rules\n"
        "1. Use ONLY the provided columns.\n"
        "2. Return VALID JSON only. No markdown.\n"
        "3. If the query cannot be answered with the columns, return an empty plan or best guess.\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Query: {query}"}
    ]

    response = call_llm(messages, model="gemini-2.5-flash")
    
    try:
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return json.loads(cleaned)
    except Exception as e:
        print(f"Plan generation failed: {e}")
        return {}
