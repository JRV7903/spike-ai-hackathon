from app.ga4.client import GA4Client
from app.ga4.planner import plan_report
from app.ga4.field_allowlist import ALLOWED_METRICS, ALLOWED_DIMENSIONS
from app.llm import call_llm
import json


class AnalyticsAgent:
    def __init__(self, property_id: str):
        self.property_id = property_id


    def run(self, query: str) -> dict:
        try:
            plan = plan_report(query)

            metrics = plan["metrics"]
            dimensions = plan["dimensions"]
            date_ranges = plan["date_ranges"]

            for m in metrics:
                if m["name"] not in ALLOWED_METRICS:
                    raise ValueError(f"Invalid metric: {m['name']}")

            for d in dimensions:
                if d["name"] not in ALLOWED_DIMENSIONS:
                    raise ValueError(f"Invalid dimension: {d['name']}")

            client = GA4Client(property_id=self.property_id)

            ga4_request = {
                "metrics": metrics,
                "dimensions": dimensions,
                "date_ranges": date_ranges,
                "limit": 1000,
            }

            response = client.run_report(ga4_request)

            structured_data = []

            if response and response.rows:
                for row in response.rows:
                    record = {}

                    for i, dim in enumerate(row.dimension_values):
                        record[dimensions[i]["name"]] = dim.value

                    for i, met in enumerate(row.metric_values):
                        record[metrics[i]["name"]] = met.value

                    structured_data.append(record)

            if not structured_data:
                return {
                    "answer": (
                        "The GA4 query executed successfully, but no data was returned. "
                        "This usually happens for new or low-traffic properties."
                    ),
                    "data": [],
                }

            preview = structured_data[:20]

            explanation = call_llm(
                [
                    {
                        "role": "system",
                        "content": (
                            "You are a GA4 analytics expert. "
                            "Explain trends clearly and conservatively."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Query: {query}\n\nData:\n{json.dumps(preview, indent=2)}",
                    },
                ]
            )

            return {
                "answer": explanation,
                "data": structured_data,
            }

        except Exception as e:
            return {
                "answer": (
                    "An internal error occurred while processing the analytics request. "
                    "Please check your query or try again later."
                ),
                "data": [],
                "error": f"AnalyticsAgent Error: {str(e)}",
            }


def run_analytics_agent(property_id: str, query: str) -> dict:
    return AnalyticsAgent(property_id).run(query)
