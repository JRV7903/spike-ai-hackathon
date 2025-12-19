from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest
from google.oauth2 import service_account
import os

class GA4Client:
    def __init__(self, property_id: str):
        self.property_id = property_id
        self.client = self._init_client()

    def _init_client(self):
        credentials_path = "credentials.json"
        if not os.path.exists(credentials_path):
            raise FileNotFoundError("credentials.json not found at project root")

        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"]
        )
        return BetaAnalyticsDataClient(credentials=credentials)

    def run_report(self, report_plan: dict):
        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            **report_plan
        )
        return self.client.run_report(request)
