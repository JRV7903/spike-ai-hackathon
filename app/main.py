from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
load_dotenv()

from app.schemas import QueryRequest, QueryResponse
from app.orchestrator import handle_query

app = FastAPI()

@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    """
    Evaluator-facing endpoint for natural language queries.
    """
    return handle_query(request)
