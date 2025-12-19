import json
from app.schemas import QueryRequest, QueryResponse
from app.agents.analytics_agent import run_analytics_agent
from app.agents.seo_agent import run_seo_agent
from app.llm import call_llm
from app.fusion import fuse_data

class Orchestrator:
    def __init__(self):
        pass

    def route_request(self, query: str, property_id: str = None) -> dict:
        system_prompt = (
            "You are an orchestration layer for a marketing data system.\n"
            "Analyze the user query and determine which agents are needed.\n"
            "Available Agents:\n"
            "- 'analytics': Google Analytics 4. Handles traffic, sessions, users, page views, bounce rates, etc. REQUIRES property_id.\n"
            "- 'seo': SEO Audit. Handles technical SEO, title tags, meta descriptions, status codes, indexability, etc.\n\n"
            "Rules:\n"
            "1. If 'Property ID Provided' is 'No', you MUST NOT select 'analytics'.\n"
            "2. If the query clearly asks for analytics but no property ID is present, return an empty list or just 'seo' if relevant, but do not hallucinate analytics capability.\n"
            "3. Return a JSON object with a list of 'agents' to call.\n"
            "4. Example: {\"agents\": [\"analytics\", \"seo\"]}\n"
        )
        
        user_prompt = f"Query: {query}\nProperty ID Provided: {'Yes' if property_id else 'No'}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_str = call_llm(messages, model="gemini-2.5-flash")
        
        try:
            cleaned = response_str.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            plan = json.loads(cleaned)
            agents_to_call = plan.get("agents", [])
        except:
            agents_to_call = []

        results = {}
        
        if "analytics" in agents_to_call and property_id:
            results["analytics"] = run_analytics_agent(property_id, query)
        
        if "seo" in agents_to_call:
            results["seo"] = run_seo_agent(query)
            
        if not results:
            if not property_id and "analytics" in query.lower():
                 return {
                    "answer": "To answer analytics questions, a GA4 Property ID is required. Please provide one.",
                    "data": []
                }
            
            return {
                "answer": "I could not determine how to answer that question with the available tools or missing credentials.",
                "data": []
            }
            
        if len(results) == 1:
            key = list(results.keys())[0]
            return results[key]
            
        analytics_data = results.get("analytics", {}).get("data", [])
        seo_data = results.get("seo", {}).get("data", [])
        
        fusion_result = fuse_data(analytics_data, seo_data)
        fused_data = fusion_result["fused_data"]
        fusion_log = fusion_result["fusion_log"]
        
        data_preview = str(fused_data)[:2000]
        
        fusion_prompt = (
            "You are a Senior Data Analyst. Synthesize a final answer based on the fused data.\n"
            f"User Query: {query}\n"
            f"Fusion Log: {fusion_log}\n"
            f"Fused Data (Preview): {data_preview}\n\n"
            "Instructions:\n"
            "1. Use the Fused Data to answer the query.\n"
            "2. If the Fusion Log indicates failure or empty data, explain why (e.g. 'Could not match URLs between GA4 and SEO data').\n"
            "3. Provide a clear, concise natural language summary.\n"
            "4. If the user requested JSON format explicitly, ensure the text explanation mentions that the data is attached.\n"
        )
        
        final_answer = call_llm([{"role": "user", "content": fusion_prompt}], model="gemini-2.5-flash")
        
        return {
            "answer": final_answer,
            "data": fused_data
        }

def handle_query(request: QueryRequest) -> QueryResponse:
    orchestrator = Orchestrator()
    result = orchestrator.route_request(request.query, request.propertyId)
    return QueryResponse(
        answer=result.get("answer", "No answer generated."),
        data=result.get("data", [])
    )
