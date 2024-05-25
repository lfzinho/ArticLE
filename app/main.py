from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from typing import List
from llm_model import LLMModel
from search_engine import SearchEngine
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Initialize FastAPI app
app = FastAPI()

# Initialize search engine and LLM model
DATA_DIR = "./data/"
DATA_FILES = ["arxiv-metadata-oai-snapshot.json"]
SPLIT_SIZE_LIMIT = 100

search_engine = SearchEngine()
search_engine.feed_json(DATA_DIR, DATA_FILES, SPLIT_SIZE_LIMIT)
model = LLMModel()

class QueryRequest(BaseModel):
    query: str
    response_type: str

@app.post("/run_query")
def run_query(request: QueryRequest):
    docs = search_engine.search(request.query)
    if docs.empty:
        raise HTTPException(status_code=404, detail="No documents found")
    
    response = model.generate_response(request.query, docs, request.response_type)
    for doc in response:
        doc['link'] = "#"  # Update with actual link if available
    return response

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI server!"}

if __name__ == "__main__":
    import uvicorn
    # on save reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
