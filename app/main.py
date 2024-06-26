from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm_model import LLMModel
from search_engine import SearchEngine
# from search_engine_cloud import SearchEngine
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
endpoint = "https://eb38f856.cc1e1530.z.vespa-app.cloud/"
application = ""

cert_path = (
    Path.home()
    / ".vespa"
    / "article.hybridsearch.default/data-plane-public-cert.pem"
)
key_path = (
    Path.home()
    / ".vespa"
    / "article.hybridsearch.default/data-plane-private-key.pem"
)


# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize search engine and LLM model
DATA_DIR = "./data/"
DATA_FILES = ["arxiv-metadata-oai-snapshot.json"]
SPLIT_SIZE_LIMIT = 100

# local vespa
search_engine = SearchEngine()
search_engine.feed_json(DATA_DIR, DATA_FILES, SPLIT_SIZE_LIMIT)

# vespa cloud
# search_engine = SearchEngine(endpoint, cert_path, key_path)


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
        doc['link'] = "#"
    return response

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI server!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# python main.py