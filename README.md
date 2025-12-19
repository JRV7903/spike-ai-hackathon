# Spike AI Hackathon Submission

## Overview

This repository contains a multi-agent backend system designed to answer natural language queries regarding Google Analytics 4 (GA4) and Technical SEO data. The system utilizes an orchestrator pattern to route queries to specialized agents and fuses data when cross-domain insights are required.

## Architecture

The application is built with **FastAPI** and follows a modular architecture:

-   **Orchestrator (`app/orchestrator.py`)**: Central entry point. Analyzes query intent, routes requests to appropriate agents, and handles data fusion.
-   **Analytics Agent (`app/agents/analytics_agent.py`)**: Interfaces with the Google Analytics Data API (v1beta). Supports dynamic property IDs and strictly allowlisted metrics/dimensions.
-   **SEO Agent (`app/agents/seo_agent.py`)**: Interfaces with Google Sheets via `gspread`. Implements a secure, structured query planner to execute logic without unsafe code evaluation.
-   **Fusion Layer (`app/fusion.py`)**: Programmatically joins datasets from disparate sources based on normalized URL keys.

## Agents

### 1. Analytics Agent (Tier 1)
-   **Source**: Google Analytics 4 Data API.
-   **Capabilities**: Traffic, user engagement, session data, page views.
-   **Security**: Uses a strict allowlist for metrics and dimensions to prevent hallucination or invalid API calls.
-   **Configuration**: Accepts `propertyId` dynamically per request.

### 2. SEO Agent (Tier 2)
-   **Source**: Google Sheets (Screaming Frog exports).
-   **Capabilities**: Status codes, meta tags, word counts, indexability.
-   **Security**: Replaces `exec()` with a structured JSON execution plan. The LLM generates a plan (filters, aggregations), which is executed safely by pandas.
-   **Configuration**: Spreadsheet ID is resolved at runtime via `SEO_SPREADSHEET_ID` environment variable or `seo_config.json`.

### 3. Orchestrator & Fusion (Tier 3)
-   **Routing**: Determines if a query requires Analytics, SEO, or both.
-   **Fusion**: Performs inner joins on normalized URL paths (e.g., matching `/pricing` from GA4 with `https://site.com/pricing` from SEO).
-   **Output**: Returns a synthesized natural language answer alongside raw structured data.

## API Contract

**Endpoint**: `POST /query`
**Port**: `8080`

### Request
```json
{
  "query": "What are the top 5 pages by views and their title tags?",
  "propertyId": "123456789"
}
```
*Note: `propertyId` is optional for SEO-only queries but required for Analytics.*

### Response
```json
{
  "answer": "The top 5 pages are...",
  "data": [
    { "pagePath": "/home", "screenPageViews": 5000, "title": "Home Page" },
    ...
  ]
}
```

## Setup & Deployment

The system is designed to be self-contained and deployed via the provided shell script.

### Prerequisites
1.  **Credentials**: Place a valid Google Service Account JSON key at the repository root named `credentials.json`.
2.  **Environment**: Linux/Unix environment with Python 3 installed.

### Deployment
Run the deployment script:
```bash
./deploy.sh
```

This script will:
1.  Create a virtual environment (`.venv`) at the repository root.
2.  Activate the environment.
3.  Install dependencies from `requirements.txt`.
4.  Start the `uvicorn` server in the background on port **8080**.
5.  Verify the process is running.

## Configuration

### Google Analytics
-   The `propertyId` is passed dynamically in the API request body.

### SEO Data
-   **Environment Variable**: Set `SEO_SPREADSHEET_ID` to the target Google Sheet ID.
-   **Config File**: Alternatively, update `seo_config.json` at the root.
-   **Sheet Name**: Defaults to `internal_all` unless overridden by `SEO_SHEET_NAME`.

## Assumptions & Limitations

-   **Data Fusion**: Fusion relies on exact URL path matching after normalization. Pages missing from either dataset will be excluded from joined results.
-   **Rate Limits**: The system uses `tenacity` for retries but is subject to standard Google API quotas.
-   **Memory**: Data processing is performed in-memory using pandas; extremely large datasets (>1GB) may require scaling resources.
