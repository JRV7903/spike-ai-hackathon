import pandas as pd
import json
import os
import gspread
from google.oauth2.service_account import Credentials
from app.llm import call_llm
from app.agents.seo_planner import plan_seo_query
from app.agents.seo_executor import execute_seo_plan

# CONFIGURATION
CONFIG_FILE = "seo_config.json"

def get_seo_config():
    """
    Resolves configuration from Env Vars -> Config File -> Defaults.
    """
    # 1. Environment Variables (Highest Priority)
    env_id = os.environ.get("SEO_SPREADSHEET_ID")
    env_name = os.environ.get("SEO_SHEET_NAME")

    if env_id:
        return {"spreadsheet_id": env_id, "sheet_name": env_name or "internal_all"}

    # 2. Config File
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return {
                    "spreadsheet_id": config.get("spreadsheet_id"),
                    "sheet_name": config.get("sheet_name", "internal_all")
                }
        except Exception as e:
            print(f"Warning: Failed to read {CONFIG_FILE}: {e}")

    # 3. Fallback / Failure
    return None

class SEOAgent:
    def __init__(self):
        """
        Initialize the SEO Agent with Google Sheets client.
        We use the same credentials.json as the Analytics Agent.
        """
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.credentials_path = "credentials.json"
        self.client = self._authenticate()

    def _authenticate(self):
        """
        Authenticates using the service account credentials.
        """
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(f"{self.credentials_path} not found.")
        
        creds = Credentials.from_service_account_file(
            self.credentials_path, scopes=self.scopes
        )
        return gspread.authorize(creds)

    def _get_data(self) -> pd.DataFrame:
        """
        Fetches data dynamically from the Google Sheet.
        """
        config = get_seo_config()
        
        if not config or not config.get("spreadsheet_id"):
            raise ValueError("SEO Spreadsheet ID is not configured. Set SEO_SPREADSHEET_ID env var or 'seo_config.json'.")

        spreadsheet_id = config["spreadsheet_id"]
        sheet_name = config["sheet_name"]

        try:
            sheet = self.client.open_by_key(spreadsheet_id).worksheet(sheet_name)
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            
            # Normalize columns: lowercase and strip spaces for schema-agnosticism
            df.columns = [c.lower().strip() for c in df.columns]
            return df
        except Exception as e:
            raise RuntimeError(f"Failed to fetch data from Google Sheet ({spreadsheet_id}): {str(e)}")


    def run(self, query: str) -> dict:
        try:
            df = self._get_data()
            
            if df.empty:
                return {
                    "answer": "The SEO dataset is empty.",
                    "data": []
                }

            columns = list(df.columns)
            
            plan = plan_seo_query(query, columns)
            
            data = execute_seo_plan(df, plan)
            
            data_preview = str(data)[:1500]
            
            explain_prompt = (
                "You are an SEO Analyst. Explain the following data in response to the user's query.\n"
                f"Query: {query}\n"
                f"Data: {data_preview}\n\n"
                "Provide a clear, concise natural language answer."
            )
            
            explanation = call_llm([{"role": "user", "content": explain_prompt}], model="gemini-2.5-flash")
            
            return {
                "answer": explanation,
                "data": data
            }

        except Exception as e:
            return {
                "answer": f"An error occurred while processing the SEO request: {str(e)}",
                "data": [],
                "error": str(e)
            }

def run_seo_agent(query: str) -> dict:
    return SEOAgent().run(query)
